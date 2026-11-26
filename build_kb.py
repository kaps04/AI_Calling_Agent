
import chromadb
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Create persistent vector database
client = chromadb.PersistentClient(
    path=str(BASE_DIR / "vector_db")
)

# Create or load collection
collection = client.get_or_create_collection(
    name="company_knowledge"
)

# Locate knowledge documents
knowledge_dir = BASE_DIR / "knowledge"

# Read all text files
for file in sorted(knowledge_dir.glob("*.txt")):

    text = file.read_text(encoding="utf-8")

    # Divide text into small chunks
    chunks = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # Store each chunk
    for i, chunk in enumerate(chunks):

        collection.upsert(
            ids=[f"{file.stem}_{i}"],
            documents=[chunk],
            metadatas=[
                {"source": file.name}
            ]
        )

    print(f"Indexed: {file.name}")

print("Knowledge base created successfully!")
print("Total chunks:", collection.count())
