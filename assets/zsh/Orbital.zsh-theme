# A compact, single-line prompt. Prompt escapes also work in async Git output.
PROMPT='%F{cyan}%~%f$(git_prompt_info) %F{yellow}›%f '
ZSH_THEME_GIT_PROMPT_PREFIX=' %F{blue}['
ZSH_THEME_GIT_PROMPT_SUFFIX=']%f'
ZSH_THEME_GIT_PROMPT_DIRTY=' %F{yellow}*%f'
ZSH_THEME_GIT_PROMPT_CLEAN=''
