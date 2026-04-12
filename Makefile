SKILLS_DIR := $(HOME)/.claude/skills
STOW_DIR   := $(dir $(CURDIR))
PKG        := $(notdir $(CURDIR))

link:
	@mkdir -p $(SKILLS_DIR)
	stow -v -t $(SKILLS_DIR) -d $(STOW_DIR) $(PKG)

unlink:
	stow -v -D -t $(SKILLS_DIR) -d $(STOW_DIR) $(PKG)

relink:
	stow -v -R -t $(SKILLS_DIR) -d $(STOW_DIR) $(PKG)

.PHONY: link unlink relink
