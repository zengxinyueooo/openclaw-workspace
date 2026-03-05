# SKILL.md for Image Generation

## name
image-generator

## description
Generates an image by calling the BananaPro API. Takes a prompt as input, and can optionally take a list of reference picture URLs.

## usage
To use this skill, the agent will execute the `run.sh` script located in the same directory.
The script expects one or two arguments:
1.  `prompt`: A string describing the desired image. (Mandatory)
2.  `reference_pics`: An optional, comma-separated string of reference picture URLs.

Example (with reference pic):
`exec(command="./run.sh '''将参考图中人物的黑丝变成白丝''' '''https://p0.meituan.net/dzusergrowthcontent/6bdf133de9352c38fed3291e8aafaf8c2281819.png'''")`

Example (without reference pic):
`exec(command="./run.sh '''画一个可爱的粉色小猫'''")`
