# A build script for building customized version of JetBrains Mono.
# Currently it handles only TTF fonts by:
# - removing the hinting information
# - freezing 'zero' OpenType feature (slashed zero is more readable)
# - revert the old design of the uppercase letter J

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from fontTools.ttLib import TTFont


NO_HINTING = True
OPENTYPE_FEATURES_TO_FREEZE = ["calt", "zero"]


def unhint(input_font: str, output_font: str):
    # Load the font
    font = TTFont(input_font)

    # Strip TrueType based hinting information
    tt_hinting_tables = ["fpgm", "prep", "cvt ", "gasp"]
    for table in tt_hinting_tables:
        if table in font:
            print(f"Strpping TrueType table [{table}] from `{input_font}`")
            del font[table]

    # Also, clear the "ttfautohint" information from the version string
    name_table = font["name"]
    for record in name_table.names:
        string_value = record.toUnicode()
        if "ttfautohint" in string_value.lower():
            # `Version 2.305; ttfautohint (v1.8.4.16-eb64)`
            cleaned_value = string_value.split(";")[0].strip()
            record.string = cleaned_value.encode(record.getEncoding())

    font.save(output_font)


def freeze_opentype_features(input_font: str, output_font: str, features: List[str]):
    features_argument = f"{','.join(x for x in features)}"

    print(f"Freezing OpenType Features [{features_argument}] into `{output_font}`...")

    subprocess.run(["pyftfeatfreeze", "-f", features_argument, input_font, output_font])


def build_fonts():
    shutil.rmtree("fonts", ignore_errors=True)

    # build fonts
    command = ["gftools", "builder", "sources/config.yaml"]

    print("Building fonts for processing...")
    try:
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

    except subprocess.CalledProcessError as e:
        print(f"Building failed with exit code {e.returncode}.", file=sys.stderr)
        print("stderr: ", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        print("stdout: ", file=sys.stderr)
        print(e.stdout, file=sys.stderr)


def patch_old_uppercase_j(
    old_font_path: str, new_font_path: str, output_font_path: str
):
    old_font = TTFont(old_font_path)
    new_font = TTFont(new_font_path)

    old_j_name = old_font.getBestCmap().get(0x004A)
    new_j_name = new_font.getBestCmap().get(0x004A)

    old_glyph = old_font["glyf"][old_j_name]
    old_metrics = old_font["hmtx"][old_j_name]

    new_glyph = new_font["glyf"][new_j_name]

    new_glyph.coordinates = old_glyph.coordinates
    new_glyph.flags = old_glyph.flags
    new_glyph.endPtsOfContours = old_glyph.endPtsOfContours

    if hasattr(new_glyph, "components"):
        del new_glyph.components
    new_glyph.numberOfContours = old_glyph.numberOfContours

    new_glyph.recalcBounds(new_font["glyf"])

    new_font["hmtx"][new_j_name] = old_metrics

    for g_name in new_font["glyf"].keys():
        if g_name.startswith(f"{new_j_name}.") or g_name == "J.alt":
            tgt = new_font["glyf"][g_name]
            tgt.coordinates = old_glyph.coordinates
            tgt.flags = old_glyph.flags
            tgt.endPtsOfContours = old_glyph.endPtsOfContours
            if hasattr(tgt, "components"):
                del tgt.components
            tgt.numberOfContours = old_glyph.numberOfContours
            tgt.recalcBounds(new_font["glyf"])
            new_font["hmtx"][g_name] = old_metrics

    new_font.save(output_font_path)
    old_font.close()
    new_font.close()
    print(
        f"Saved patched font with old design of the uppercase letter J: [{output_font_path}]"
    )


def process_fonts():
    input_path = Path("fonts/ttf")
    output_path = input_path

    if NO_HINTING:
        output_path = input_path.joinpath("unhinted")
        shutil.rmtree(output_path, ignore_errors=True)
        output_path.mkdir(parents=True)

    for file in input_path.iterdir():
        if file.is_file():
            if NO_HINTING:
                unhint(str(file), str(output_path.joinpath(file.name)))

    input_path = output_path
    output_path = output_path.joinpath("frozen")
    shutil.rmtree(output_path, ignore_errors=True)
    output_path.mkdir(parents=True)

    for file in input_path.iterdir():
        if file.is_file():
            freeze_opentype_features(
                str(file),
                str(output_path.joinpath(file.name)),
                OPENTYPE_FEATURES_TO_FREEZE,
            )

    print(f"Done! Process fonts are located at `{output_path}`")

    patched_fonts_output_path = Path("patched_fonts")
    shutil.rmtree(patched_fonts_output_path, ignore_errors=True)
    patched_fonts_output_path.mkdir()

    print(output_path)

    for font in output_path.iterdir():  # frozen fonts
        if font.is_file():
            print(font)
            old_font = Path(f"old_fonts/{font.name}")
            print(
                f"Patching the frozen font [{str(font)}] with the uppercase letter J from the old font..."
            )

            patch_old_uppercase_j(
                str(old_font),
                str(font),
                str(patched_fonts_output_path.joinpath(font.name)),
            )


def main():
    build_fonts()
    process_fonts()


if __name__ == "__main__":
    main()
