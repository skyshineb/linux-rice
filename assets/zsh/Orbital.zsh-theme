# A compact, single-line prompt. Oh My Zsh calls git_prompt_info only inside Git repos.
PROMPT='%{$fg[cyan]%}%~%{$reset_color%}$(git_prompt_info) %{$fg[yellow]%}›%{$reset_color%} '
ZSH_THEME_GIT_PROMPT_PREFIX=' %{$fg[blue]%}['
ZSH_THEME_GIT_PROMPT_SUFFIX=']%{$reset_color%}'
ZSH_THEME_GIT_PROMPT_DIRTY=' %{$fg[yellow]%}*%{$reset_color%}'
ZSH_THEME_GIT_PROMPT_CLEAN=''
