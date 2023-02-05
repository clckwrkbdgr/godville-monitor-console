PROJECT=pygod
TR=tr
LOCALES=ru uk
TR_DIR=share
SOURCES=$(wildcard *.py monitor/*/*.py)

INSTALL_DIR=$(XDG_DATA_HOME)/$(PROJECT)
PO_FILES=$(LOCALES:%=$(TR_DIR)/%/LC_MESSAGES/$(PROJECT).po)
MO_FILES=$(PO_FILES:%.po=%.mo)

all: mo

install: $(DEST_MO_FILES)
	install -D $(TR_DIR)/ru/LC_MESSAGES/$(PROJECT).mo $(INSTALL_DIR)/ru/LC_MESSAGES/$(PROJECT).mo
	install -D $(TR_DIR)/uk/LC_MESSAGES/$(PROJECT).mo $(INSTALL_DIR)/uk/LC_MESSAGES/$(PROJECT).mo

mo: $(MO_FILES)

%.mo: %.po
	pybabel compile -f -i $< -o $@

po: $(PO_FILES)

%.po: $(PROJECT).pot
	@if [ -f $@ ]; then \
		pybabel update -N -i $< -D $(PROJECT) -d $(TR_DIR) -l $(@:$(TR_DIR)/%/LC_MESSAGES/$(PROJECT).po=%); \
	else \
		pybabel init      -i $< -D $(PROJECT) -d $(TR_DIR) -l $(@:$(TR_DIR)/%/LC_MESSAGES/$(PROJECT).po=%); \
	fi

$(PROJECT).pot: $(SOURCES)
	@pybabel extract --omit-header --no-wrap -k $(TR) -o $@ .

clean:
	$(RM) $(PROJECT).pot
