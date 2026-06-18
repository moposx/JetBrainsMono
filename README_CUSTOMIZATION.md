# Build Customized JetBrains Mono

For my own customization, you need:

- JetBrains Mono v2.251 (or any published version prior to v2.300), in which there's still the old design of the uppercase letter J.

Put old fonts in to directory `old_fonts` in the project root.

Inside a virtual environment:

- Install dependencies: `pip install -r requirements.txt`
- Run custom build script: `python ./custom.py`

Find the output in `patched_fonts` directory in the project root.
