<div align="center">

<img src="io.github.dantavares.f3-gui.svg" width="96" alt="F3 GUI icon"/>

# F3 GUI

**Interface gráfica para o [Fight Flash Fraud (f3)](https://github.com/AltraMayor/f3)**

Detecte e corrija pen drives e cartões de memória que mentem sobre sua capacidade real.

[![Licença: GPL v3](https://img.shields.io/badge/Licen%C3%A7a-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://python.org)
[![Plataforma](https://img.shields.io/badge/Plataforma-Linux-orange.svg)]()
[![Flathub](https://img.shields.io/badge/Flathub-em%20breve-blueviolet.svg)]()

![Screenshot da aplicação](screenshots/main.png)

</div>

---

## ✨ Funcionalidades

- **Detecção automática** de dispositivos de armazenamento removíveis (pendrives, cartões SD)
- **Sincronização** automática entre dispositivo e ponto de montagem
- **Veredito claro** ao final da verificação: ✅ dispositivo genuíno ou ⛔ tamanho falso
- **Captura automática** do parâmetro `--last-sec` do f3probe para uso direto no f3fix
- **Terminal integrado** com saída em tempo real e coloração por tipo de mensagem
- **Barras de progresso** para escrita e leitura
- Painel de controles **rolável** — funciona em qualquer resolução de tela

---

## 🐛 Bug Conhecido
* As Barras de "Escrita" e "Leitura" não estão funcionando
* As saídas (stdout) não aparecem em tempo real e as vezes com caracteres estranhos

## 🛠️ Pré-requisitos

### f3 (Fight Flash Fraud)

```bash
# Debian / Ubuntu / Linux Mint
sudo apt install f3

# Arch Linux
sudo pacman -S f3

# Fedora
sudo dnf install f3

# Windows
Senta no colo do Bill Gates e chora
```

### Python 3 + Tkinter

```bash
# Debian / Ubuntu
sudo apt install python3 python3-tk

# Arch Linux
sudo pacman -S python tk

# Fedora
sudo dnf install python3 python3-tkinter
```

---

## 🚀 Como usar

```bash
# Clone o repositório
git clone https://github.com/SEUUSUARIO/f3-gui.git
cd f3-gui

# Execute
python3 f3_gui.py
```

> **Atenção:** `f3probe` e `f3fix` precisam de privilégios de root para acessar o dispositivo diretamente. Execute com `sudo python3 f3_gui.py` caso necessário, ou configure o `polkit` para permitir acesso sem senha.

---

## 📋 Fluxo de trabalho recomendado

```
1. Conecte o dispositivo suspeito
2. Clique em  ↺ Atualizar lista  para detectá-lo
3. Selecione o dispositivo no dropdown
4. Execute f3write  →  grava arquivos de teste
5. Execute f3read   →  verifica a integridade
                        (veredito aparece automaticamente)
6. Se falso:
   └─ Execute f3probe  →  detecta capacidade real e captura --last-sec
   └─ Execute f3fix    →  corrige a tabela de partições
```

### O que cada ferramenta faz

| Ferramenta | O que faz | Precisa de root? |
|-----------|-----------|:---:|
| `f3write` | Grava arquivos numerados até encher o dispositivo | Não |
| `f3read`  | Lê os arquivos e verifica integridade — dá o veredito final | Não |
| `f3probe` | Sonda a capacidade real sem precisar encher o dispositivo | **Sim** |
| `f3fix`   | Corrige a tabela de partições para refletir o tamanho real | **Sim** |

---

## 📦 Instalação via Flatpak (em breve)

---

## 📄 Licença

Distribuído sob a licença **GPL-3.0**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 🙏 Créditos

- [Michel Machado](https://github.com/AltraMayor/f3) — criador do f3 (Fight Flash Fraud)
- Interface gráfica desenvolvida com Python e Tkinter
