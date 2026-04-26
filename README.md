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

Pra voltar ao normal depois:

sudo setcap -r /usr/bin/tcpdump

### Pro celular

**Configurando o Termux:**

Primeiramente, baixei o Termux, só vai na playstore e baixa. Posteriomente, execute os seguintes comandos:
```
pkg update && pkg upgrade
pkg install proot-distro
proot-distro install archlinux
proot-distro login archlinux
```
Instale a distro referente ao local onde roda o seu Fedt server. Recomendo isso para evitar erros por conflitos de versão, coloquei a do arch, pois, essa é a distro que utilizo.

**Configurando o Ambiente:**

Atualize o sistema ao entrar nele. E instale as dependências necessárias, pode váriar de distro para distro, mas a do Arch é assim.
```
pacman -Syu
pacman -S git
git clone https://github.com/Julio-C-Oliveira/gercom_fedt-distributed.git
cd gercom_fedt-distributed
pacman -S python
python -m venv .venv
source .venv/bin/activate
pip install .
```
Após as instalações, é só rodar o cliente da mesma forma que no computador.

**TO-DO:**

- Resolver a captura de cpu e ram. Atualmente só está capturando o dos clientes que rodam no PC, tenho que capturar os do Raspberry e do Android e posteriormente unificar em um arquivo único dos clientes.