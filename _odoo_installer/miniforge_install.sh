#!/bin/bash
# Miniforge Path for Python Environment
MF_PATH="/etc/miniforge"
BASHRC_ROOT="/etc/bash.bashrc"
FISHCONFIG="/etc/fish/config.fish"
ZSHRC="/etc/zsh/zshrc"

install_miniforge() {
    echo -e "\n---- Install Miniforge ----"
    wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    chmod +x Miniforge3-$(uname)-$(uname -m).sh
    ./Miniforge3-$(uname)-$(uname -m).sh -b -f -p $MF_PATH
    
    # Configure for Bash
    if [ -f "$BASHRC_ROOT" ]; then
        configure_bash
    fi
    
    # Configure for Fish
    if [ -f "$FISHCONFIG" ]; then
        configure_fish
    fi
    
    # Configure for Zsh
    if [ -f "$ZSHRC" ]; then
        configure_zsh
    fi
}

configure_bash() {
    sed -i.bak '/# >>> conda initialize >>>/,/# <<< conda initialize <<</d' "$BASHRC_ROOT"
    {
        echo ""
        echo "# >>> conda initialize >>>"
        echo "# Contents within this block are managed by 'conda init' "
        echo "__conda_setup=\"\$(${MF_PATH}/bin/conda 'shell.bash' 'hook' 2> /dev/null)\""
        echo "if [ \$? -eq 0 ]; then"
        echo "    eval \"\$__conda_setup\""
        echo "else"
        echo "    if [ -f \"${MF_PATH}/etc/profile.d/conda.sh\" ]; then"
        echo "        . \"${MF_PATH}/etc/profile.d/conda.sh\""
        echo "    else"
        echo "        export PATH=\"${MF_PATH}/bin:\$PATH\""
        echo "    fi"
        echo "fi"
        echo "unset __conda_setup"
        echo ""
        echo "if [ -f \"${MF_PATH}/etc/profile.d/mamba.sh\" ]; then"
        echo "    . \"${MF_PATH}/etc/profile.d/mamba.sh\""
        echo "fi"
        echo "# <<< conda initialize <<<"
        echo "conda config --set auto_activate_base false"
    } >> "$BASHRC_ROOT"
}

configure_fish() {
    sed -i.bak '/# >>> conda initialize >>>/,/# <<< conda initialize <<</d' "$FISHCONFIG"
    {
        echo ""
        echo "# >>> conda initialize >>>"
        echo "eval ${MF_PATH}/bin/conda 'shell.fish' 'hook' \$argv | source"
        echo "if test -f \"${MF_PATH}/etc/fish/conf.d/mamba.fish\""
        echo "    source \"${MF_PATH}/etc/fish/conf.d/mamba.fish\""
        echo "end"
        echo "# <<< conda initialize <<<"
        echo "conda config --set auto_activate_base false"
    } >> "$FISHCONFIG"
}

configure_zsh() {
    sed -i.bak '/# >>> conda initialize >>>/,/# <<< conda initialize <<</d' "$ZSHRC"
    {
        echo ""
        echo "# >>> conda initialize >>>"
        echo "# Contents within this block are managed by 'conda init' "
        echo "__conda_setup=\"\$(${MF_PATH}/bin/conda 'shell.zsh' 'hook' 2> /dev/null)\""
        echo "if [ \$? -eq 0 ]; then"
        echo "    eval \"\$__conda_setup\""
        echo "else"
        echo "    if [ -f \"${MF_PATH}/etc/profile.d/conda.sh\" ]; then"
        echo "        . \"${MF_PATH}/etc/profile.d/conda.sh\""
        echo "    else"
        echo "        export PATH=\"${MF_PATH}/bin:\$PATH\""
        echo "    fi"
        echo "fi"
        echo "unset __conda_setup"
        echo ""
        echo "if [ -f \"${MF_PATH}/etc/profile.d/mamba.sh\" ]; then"
        echo "    . \"${MF_PATH}/etc/profile.d/mamba.sh\""
        echo "fi"
        echo "# <<< conda initialize <<<"
        echo "conda config --set auto_activate_base false"
    } >> "$ZSHRC"
}

main() {
    install_miniforge
}

main