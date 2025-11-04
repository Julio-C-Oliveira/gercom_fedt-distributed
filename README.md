### Compilar os arquivos a partir do proto
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    --mypy_out=. \
    ./fedT.proto
