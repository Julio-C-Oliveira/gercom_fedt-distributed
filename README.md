The data used in this project come from the **“Appliances Energy Prediction”** dataset, published by:

> **Candanedo, L. (2017).**  
> *Appliances Energy Prediction* [Dataset].  
> **UCI Machine Learning Repository.**  
> DOI: [10.24432/C5VC8G](https://doi.org/10.24432/C5VC8G)

The dataset is publicly available at the **UCI Machine Learning Repository**:  
🔗 [https://archive.ics.uci.edu/dataset/374/appliances+energy+prediction](https://archive.ics.uci.edu/dataset/374/appliances+energy+prediction)

**License:**  
This dataset is licensed under a **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.  
This allows for **sharing** and **adapting** the dataset for any purpose, even commercially, provided that appropriate credit is given to the original author.

### Compile from the proto file
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    --mypy_out=. \
    ./fedT.proto

### Tirar o sudo do tcpdump
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/tcpdump