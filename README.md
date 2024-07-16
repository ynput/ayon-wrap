# Wrap
A Faceform Wrap is a topology transfer tool for creation of digital characters based on 3D scans of real actors or sculpts.

As Wrap has no Python API its integration is a bit limited. It can now open predefined template workfile based on profiles. 
These template workfiles could contain placeholders which will be textually replaced before starting and opening a workfile with Wrap.

## Custom templates
Configure `ayon+settings://wrap/workfile_builder/custom_templates` to add profiles to select particular `.wrap` template for a task.

## Multi templates per task
If your use case requires usage of multiple templates for single task (imagine it as steps)
```
Example:
- ALIGN (task)
  - align scan (step)
  - align scan render
  - retouch sheet
- MODEL (task)
  - wrap (step)
```
admin needs to configure location of separate templates in `ayon+settings://wrap/multiple_templates_per_tasks`.

Inputs are type name or type and returned value is path to template.

There is also need for additional new template in `Anatomy`. It is expected to be called `wrap_multi` and would look like:
```
Directory template: {root[work]}/{project[name]}/{hierarchy}/{folder[name]}/work/{task[name]}</{template_name}>
File name template: {project[code]}_{folder[name]}_{task[name]}<_{template_name}>_{@version}.{ext}
```
That added `</{template_name}>` is important to separate workfiles for particular template into subfolders.

Artist then will be shown with new Dialog where they can select from list of templates and shown if any workfile exist for those.

## Load placeholders
Read nodes which should be controlled by AYON needs to contain `AYON.` prefix in `File name` property.

Format of the placeholder:
`AYON.FOLDER_PATH.PRODUCT_NAME.VERSION.EXTENSION`

Description:

- AYON - hardcoded prefix denoting this is Ayon placeholder
- FOLDER_PATH - points to folder
    - could be encased with {} to denote it is dynamic value `{currentFolder}` - folder from context
    - or any actual path of folder (`/characters/characterA`)
- PRODUCT_NAME - value of product from folder (`modelMain`)
- VERSION - value to select version
     - encased in {} (`{latest}`, `{hero}`) points to version of current context
     - any integer number points to specific version (`4`)
- EXTENSION - extension of loaded representation (`png`)

## Launching of Wrap

Regular artist opens Wrap ordinary via Launcher. Before Wrap is opened Scene Inventory tool will be shown to highlight which items 
were loaded when placeholders got resolved. Artist can see version, if loaded version is not the latest, 
it is highlighted by red color.

## Publish
As there is no Python API to run code of Ayon directly in Wrap application, publish process is semi-manual. 
Artists must prepare workfile, save it and then publish it via Publisher: docs/artist_tools_publisher tool.

There might be multiple write nodes inside of the workfile, but not all of them must be published via Ayon. 
Publishable nodes must contain AYON_ prefix in their names. 
Whole name has then format `AYON_PUBLISHED_PRODUCT_NAME` (eg.`AYON_wrapRenderMain` - 
this will publish wrapRenderMain product of wrap family.

Artist should open Publisher, select published context in left column, 
drag&drop prepared workfile in the middle column and hit Create. 
There should appear new instance in the right column, next step would be to hit Publish to start publishing process.

## Build process and installation
Run `create_package.py` and install addon via `Bundles` page.

This addon doesn't require any external dependencies.