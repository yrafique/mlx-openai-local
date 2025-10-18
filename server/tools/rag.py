"""
RAG (Retrieval Augmented Generation) tool for document-based Q&A.
Integrates LangChain + ChromaDB for vector storage and retrieval.
Inspired by chat-with-mlx project (MIT License).
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

# LangChain imports
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader
)
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.docstore.document import Document

# YouTube transcript
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
    HAS_YOUTUBE = True
except ImportError:
    HAS_YOUTUBE = False

# PDF processing
try:
    from pypdf import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


class RAGManager:
    """
    Manages document ingestion and retrieval for RAG.
    Uses ChromaDB for vector storage and HuggingFace embeddings.
    """

    def __init__(self, collection_name: str = "mlx_docs", persist_directory: str = "./chroma_db"):
        """
        Initialize RAG manager.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the vector database
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Initialize embeddings (using lightweight model)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Initialize or load vector store
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )

        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def ingest_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Ingest raw text into the vector database.

        Args:
            text: Text content to ingest
            metadata: Optional metadata for the document

        Returns:
            Number of chunks created
        """
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)

        # Create documents with metadata
        documents = [
            Document(page_content=chunk, metadata=metadata or {})
            for chunk in chunks
        ]

        # Add to vector store
        self.vector_store.add_documents(documents)

        return len(chunks)

    def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest a file (PDF, TXT, MD) into the vector database.

        Args:
            file_path: Path to the file

        Returns:
            Dict with ingestion results
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            # Determine loader based on file type
            if file_path.suffix.lower() == '.pdf':
                if not HAS_PDF:
                    return {"success": False, "error": "PDF support not installed. Install pypdf."}
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix.lower() in ['.txt', '.md']:
                loader = TextLoader(str(file_path))
            else:
                return {"success": False, "error": f"Unsupported file type: {file_path.suffix}"}

            # Load and split documents
            documents = loader.load()
            split_docs = self.text_splitter.split_documents(documents)

            # Add metadata
            for doc in split_docs:
                doc.metadata['source_file'] = str(file_path)
                doc.metadata['file_type'] = file_path.suffix

            # Add to vector store
            self.vector_store.add_documents(split_docs)

            return {
                "success": True,
                "file": str(file_path),
                "chunks": len(split_docs),
                "message": f"Ingested {len(split_docs)} chunks from {file_path.name}"
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to ingest file: {str(e)}"}

    def ingest_youtube(self, youtube_url: str) -> Dict[str, Any]:
        """
        Ingest YouTube video transcript into the vector database.

        Args:
            youtube_url: YouTube video URL

        Returns:
            Dict with ingestion results
        """
        if not HAS_YOUTUBE:
            return {"success": False, "error": "YouTube support not installed. Install youtube-transcript-api."}

        try:
            # Extract video ID from URL
            video_id = self._extract_youtube_id(youtube_url)
            if not video_id:
                return {"success": False, "error": "Invalid YouTube URL"}

            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

            # Combine transcript into text
            full_text = " ".join([entry['text'] for entry in transcript_list])

            # Ingest with metadata
            metadata = {
                'source': 'youtube',
                'video_id': video_id,
                'url': youtube_url
            }

            chunks = self.ingest_text(full_text, metadata)

            return {
                "success": True,
                "video_id": video_id,
                "chunks": chunks,
                "message": f"Ingested YouTube video transcript ({chunks} chunks)"
            }

        except (TranscriptsDisabled, NoTranscriptFound):
            return {"success": False, "error": "No transcript available for this video"}
        except Exception as e:
            return {"success": False, "error": f"Failed to ingest YouTube video: {str(e)}"}

    def query(self, query: str, k: int = 4) -> List[Document]:
        """
        Query the vector database for relevant documents.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of relevant documents
        """
        results = self.vector_store.similarity_search(query, k=k)
        return results

    def query_with_scores(self, query: str, k: int = 4) -> List[tuple]:
        """
        Query the vector database with relevance scores.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return results

    def clear_collection(self) -> Dict[str, Any]:
        """
        Clear all documents from the collection.

        Returns:
            Dict with operation result
        """
        try:
            # Delete and recreate collection
            self.vector_store.delete_collection()
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            return {"success": True, "message": "Collection cleared"}
        except Exception as e:
            return {"success": False, "error": f"Failed to clear collection: {str(e)}"}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.

        Returns:
            Dict with database stats
        """
        try:
            collection = self.vector_store._collection
            count = collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {"error": f"Failed to get stats: {str(e)}"}

    @staticmethod
    def _extract_youtube_id(url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats."""
        # Handle youtu.be format
        if 'youtu.be' in url:
            return url.split('/')[-1].split('?')[0]

        # Handle youtube.com format
        parsed = urlparse(url)
        if 'youtube.com' in parsed.netloc:
            if 'v' in parse_qs(parsed.query):
                return parse_qs(parsed.query)['v'][0]

        # Assume it's just the video ID
        if len(url) == 11 and '/' not in url:
            return url

        return None


# Global RAG manager instance
_rag_manager = None

def get_rag_manager() -> RAGManager:
    """Get or create the global RAG manager instance."""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager()
    return _rag_manager


# Tool definitions for OpenAI function calling
RAG_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "ingest_document",
            "description": "Ingest a document (PDF, TXT, MD) into the knowledge base for later retrieval. Use this when the user wants to add documents to the system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to ingest"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ingest_youtube",
            "description": "Ingest a YouTube video transcript into the knowledge base. Use this when the user provides a YouTube URL and wants to chat about the video content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "youtube_url": {
                        "type": "string",
                        "description": "YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)"
                    }
                },
                "required": ["youtube_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_knowledge_base",
            "description": "Search the knowledge base for relevant information. Use this when answering questions about previously ingested documents or videos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 4)",
                        "default": 4
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_knowledge_base",
            "description": "Clear all documents from the knowledge base. Use this when the user wants to start fresh.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_knowledge_base_stats",
            "description": "Get statistics about the knowledge base (number of documents, etc.). Use this when the user asks about what's in the knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


def execute_rag_tool(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a RAG tool function.

    Args:
        function_name: Name of the function to execute
        arguments: Function arguments

    Returns:
        Tool execution result
    """
    rag = get_rag_manager()

    try:
        if function_name == "ingest_document":
            return rag.ingest_file(arguments.get("file_path", ""))

        elif function_name == "ingest_youtube":
            return rag.ingest_youtube(arguments.get("youtube_url", ""))

        elif function_name == "query_knowledge_base":
            query = arguments.get("query", "")
            k = arguments.get("k", 4)
            results = rag.query_with_scores(query, k=k)

            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "score": float(score),
                    "metadata": doc.metadata
                })

            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results)
            }

        elif function_name == "clear_knowledge_base":
            return rag.clear_collection()

        elif function_name == "get_knowledge_base_stats":
            return rag.get_stats()

        else:
            return {"success": False, "error": f"Unknown function: {function_name}"}

    except Exception as e:
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}
