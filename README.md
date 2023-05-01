# Avrtar: (AltspaceVR Avatar app)
An app to help altspacer preserve avatars before Altspace shuts down.  
By [DaveVR](https://discord.com/users/425958565812109342), [Luminosity](https://discord.com/users/508212993574567958) and [Max](https://discord.com/users/548094385750016000). Special thanks to [BenG](https://discord.com/users/321369881989611522) for all the help.

## 1. Preserve My Avatars Web App
### Configure
- edit next.config.js:
    ```js
    /** @type {import('next').NextConfig} */
    const nextConfig = {
    reactStrictMode: true,
    // change the base path to the subpath of your own app
    basePath: '/avatar'
    }

    module.exports = nextConfig
    ```
- (for when you are hosting locally) reverse proxy (nginx as example):
    ```nginx
        server {
            listen 443 ssl;

            server_name $your_server_name;
            ssl_certificate $path_to_your_cert;
            ssl_certificate_key $path_to_your_certkey;

            location ^~ /avatar {
                proxy_pass http://localhost:69/avatar;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection $connection_upgrade;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header Host $host;
            }
        }
    ```
- add `.env` file:
    ```bash
    cp .env.example .env
    ```
    ```
    SERVER_PORT=69
    EMAIL=altspace_email
    PASSWORD=altspace_password
    SMTP_HOST=your_smtp_server_hostname
    SMTP_USERNAME=your_smtp_username
    SMTP_PASSWORD=your_smtp_password
    SENDER_EMAIL=send_from_which_email
    WEBHOOK_NAME=your_web_hook_name
    WEBHOOK_URL=your_web_hook_url
    ```
### Build and Run
```bash
npm install
npm run build
npm start_prod
```

### TODOs
- responsiveness
- containerize & k8s

## 2. Altspace Avatar Assembler

### Prerequisites
- for `-r` or `--rig`:  
[Auto-Rig Pro ](https://blendermarket.com/products/auto-rig-pro)(v3.67.18)
- for `-c` or `--vrc`:
  - [Cats Blender Plugin](https://github.com/absolute-quantum/cats-blender-plugin) (v0.19.1)  
(on development branch as of writting)
  - [material-combiner-addon](https://github.com/Grim-es/material-combiner-addon)  
(only one version as of writting)

### Usage
```
usage: blender.exe -b --python avatar.py -- [-h] [-i [INPUT]] [-o [OUTPUT]] [-p] [-t] [-r] [-c]

options:
  -h, --help            show this help message and exit
  -i [INPUT], --input [INPUT]
                        input filepath (default: -)
  -o [OUTPUT], --output [OUTPUT]
                        output filepath (default: Exports)
  -p, --preview         preview (default: False)
  -t, --thicc           extra thicc (default: False)
  -r, --rig             autorig (default: False)
  -c, --vrc             optimize for vrc (default: False)
```

### Example
- read customization file from stdin
```
cat example.json | blender.exe -b --python avatar.py
```

- to pass options to python, use the double-dash (`--`):
```
## The following command will: generate preview, extra thicc and autorig
blender.exe -b --python avatar.py -- \
    -i example.json \
    -o Exports/example/example.fbx \
    -p \
    -t \
    -r
```

### TODOs
- eyes and mouth for VRC

## 3. VRC Uploader
- run in batch mode:
```
Unity.exe -batchmode -nographics -executeMethod upload.AutoUpload -logFile log.txt -username yourusername -email youremail
```

# Join Us
### vrsocial.org  
[![Discord](https://img.shields.io/badge/Discord-%23CC2222.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/7DPWRYNWuC)
### freemre.com
[![Discord](https://img.shields.io/badge/Discord-%230078D7.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/yStWGYcgKJ)

---
> **Note** the models and textures are not included, they are properties of Microsoft
