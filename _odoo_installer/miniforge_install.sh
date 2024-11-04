#!/bin/bash

# Miniforge Path for Python Environment
MF_PATH="/etc/miniforge"
BASHRC_ROOT="/etc/bash.bashrc"


install_miniforge() {
    echo -e "\n---- Install Miniforge ----"
    wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    chmod +x Miniforge3-$(uname)-$(uname -m).sh
    ./Miniforge3-$(uname)-$(uname -m).sh -b -f -p $MF_PATH

    if [ -d "$MF_PATH" ]; then

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

        source $BASHRC_ROOT
    else
        echo "Miniforge path doesn't setup properly"
    fi

}


main() {
    install_miniforge
}

main