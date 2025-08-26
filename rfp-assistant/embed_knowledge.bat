


set SOURCE_DIR="../Responses"
set OUTPUT_DIR="../rfp-data"


mkdir -p OUTPUT_DIR


echo "Checking required packages..."
pip install -q langchain langchain-community langchain-openai faiss-cpu pypdf docx2txt unstructured tiktoken



python ../rfp-assistant/utils/knowledge_embedder.py %SOURCE_DIR% %OUTPUT_DIR%

echo "Embedding process complete!"
echo "Knowledge base is now ready for use with the RFP Assistant."
