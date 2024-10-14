# C3D File Importer for Blender

[Blender](https://www.blender.org/) addon for importing motion capture data found in .c3d files.

<img src="https://github.com/user-attachments/assets/eab39780-5c87-4145-bb72-d3fcf5454f4c" width=50% height=50%>

# How to Install

1. [Download](https://github.com/MattiasFredriksson/io_anim_c3d/archive/master.zip) the latest version of `io_anim_c3d` from source code (intended for latest LTS release, see [release](https://github.com/MattiasFredriksson/io_anim_c3d/releases) section for stable/specific versions).
2. Open Blender
3. Open the Edit->Preferences window.
4. Go to the 'Add-ons' tab.
5. Click the 'Install...' button.
6. Navigate to the folder containing the downloaded .zip file and double-click the file.
7. Enable the addon 'Import-Export: C3D format' in the addon window.
8. Not there? Use the refresh button, restart blender, google how to install add-ons, or visit [docs.blender.org](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html).


# How to Use

1. Make sure the add-on is installed and enabled (see the 'How to Install' section).
2. Go to File->Import->C3D (.c3d) to open the import window.
3. Change the import settings (if needed).
4. Navigate to the folder containing the .c3d file, and... 
    1. Double-click to import a single file or
    2. Select file(s) to import and click the 'Import C3D' button.

# Development

General guidelines and information how to configure the repository for development.

Development Tools
-------
- Visual Studio Code
- [Blender Development Extension](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development)

Tests
-------
Unittests are available under the 'tests/' folder. To run call:

`tests/run.sh <path or alias to Blender executable>`

Running tests require the addon to be installed to the Blender executable, simplest way to do so is to use the Blender development extension with the same executable as it will configure a symlink to the project, ensuring the test will run with the latest changes to the code.

Unittests are minimal and should focus on testing the addon functionality. For functionality testing the importer go to the underlying .c3d parser [project](https://github.com/MattiasFredriksson/py-c3d).


Code Style
-------
- Classes should be in PascalCase
- Variables and functions should be in snake_case
- Code needs to be pep8 compliant (\_\_init\_\_.py has exemptions due to Blender dependencies).

Addon Tooltip Style
-------

- Addon property names should written with the first letter in each word capatilized.
- Don't forget to exclude the dot (.) at the end of the description as it will be added automatically...

# Further Questions?

If there are any questions or suggestions please visit the [issue board](https://github.com/MattiasFredriksson/io_anim_c3d/issues) and make a ticket, hopefully I will be able to answer questions within some reasonable time frame 😄.
