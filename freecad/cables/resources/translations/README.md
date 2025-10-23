# About translating Cables Workbench

## Translators:

Translations for this workbench is done by visiting the **FreeCAD-addons**
project on CrowdIn platform at <https://crowdin.com/project/freecad-addons> webpage,
then find your language, look for the **Cables** project and do the translation.

## Maintainers:

> [!NOTE]
> All commands **must** be run in `./resources/translations` directory.

> [!NOTE]
> run ./updateTranslations.py without argument to get more usage information.

### Updating translations template file

To update the template file from source files you should use this command:

```shell
./updateTranslations.py updatets
```

### Sending translation template file to crowdin

To send the template ts file to crowdin use this command:

```shell
./updateTranslations.py upload
```

### Checking build state on crowdin

To check the project build state on a crowdin sever (e.g. last build date) use this command:

```shell
./updateTranslations.py build_status
```

### Building zip file on crowdin

To build a ready-for-download zip file on crowdin use this command:

```shell
./updateTranslations.py build
```

### Download zip file from crowdin

To download zip file created in previous step use this command:

```shell
./updateTranslations.py download
```

### Installing translations files

To unzip downloaded translations from crowdin and to create corresponding qm files use this command:

```shell
./updateTranslations.py install
```

Use this only for tests:

```shell
lrelease Cables_*.ts
```
