
import fs from 'fs';
import { NextApiRequest, NextApiResponse } from "next";
import superagent from 'superagent';
import cheerio from 'cheerio';
const { execSync } = require("child_process");
import nodemailer from "nodemailer";
const path = require("path");
const hbs = require("nodemailer-express-handlebars");
import { DiscordNotification } from '@penseapp/discord-notification'

interface Data {
    username: string;
    email: string;
    extraThicc?: boolean;
    autorig?: boolean;
}

const email = process.env.EMAIL;
const password = process.env.PASSWORD;
const webhook_name = process.env.WEBHOOK_NAME;
const webhook_url = process.env.WEBHOOK_URL;

const handlebarOptions = {
    viewEngine: {
        extName: ".handlebars",
        partialsDir: path.resolve("./src/templates/"),
        defaultLayout: false,
    },
    viewPath: path.resolve("./src/templates/"),
    extName: ".handlebars",
};

let cookie: string[] = [];
let discordNotification: DiscordNotification = new DiscordNotification(webhook_name, webhook_url);

function writeLog(message: string) {
    fs.writeFileSync("log.txt",
        message,
        {
            encoding: "utf8",
            flag: "a+",
            mode: 0o666
        });
}

export default async function AvatarApi(
    req: NextApiRequest,
    res: NextApiResponse,
) {
    const { username, email, extraThicc, autorig }: Data = req.body;
    const forwarded = req.headers["x-forwarded-for"] as string;
    const ip = forwarded ? forwarded.split(/, /)[0] : req.connection.remoteAddress

    console.log(`${email} requested ${username} (ip: ${ip}). Extra Thicc? ${extraThicc}. Autorig? ${autorig}`);
    writeLog('===============================================================================================\n');
    writeLog(`${email} requested ${username} (ip: ${ip}). Extra Thicc? ${extraThicc}. Autorig? ${autorig}\n`);
    discordNotifyRequest(username, email, ip as string, extraThicc as boolean, autorig as boolean);
    const customization = await getCustomization(username);
    if (!customization) {
        res.status(422).json({ message: "User not found, make sure to use username NOT display name (case sensitive)" });
        return;
    }
    console.log('Generating model according to customization', customization.customization);
    const dirname = encodeURIComponent(email);
    const filename = `${encodeURIComponent(username)}.fbx`;
    const numfiles = execSync(`ls Exports/${dirname}/*.fbx | wc -l`, { cwd: '../avatar' });

    if (parseInt(numfiles) > 5) {
        res.status(503).json({ message: "Exceeded limit for current email" });
        return;
    }
    try {
        writeLog(`blender.exe -b --python avatar.py -- -p -o Exports/${dirname}/${filename}${extraThicc ? ' -t' : ''}${autorig ? ' -c' : ''}\n`);
        execSync(
            `blender.exe -b --python avatar.py -- -p -o Exports/${dirname}/${filename}${extraThicc ? ' -t' : ''}${autorig ? ' -c' : ''}`,
            { cwd: '../avatar', input: customization.customization }
        );
    } catch (err) {
        res.status(500).json({ message: "Failed to generate 3D model, please contact us on discord" });
        console.log(err);
        return;
    }
    const transporter = nodemailer.createTransport({
        port: 465,
        secure: true,
        host: process.env.SMTP_HOST,
        auth: {
            user: process.env.SMTP_USERNAME,
            pass: process.env.SMTP_PASSWORD,
        },
        tls: { rejectUnauthorized: false },
    });
    transporter.use("compile", hbs(handlebarOptions));
    try {
        await transporter.sendMail({
            from: process.env.SENDER_EMAIL,
            replyTo: process.env.SENDER_EMAIL,
            to: email,
            subject: `Your avatar model is ready, ${username}`,
            // @ts-ignore-next-line
            template: "contact", //
            context: {
                username: username,
                email: email,
            },
            attachments: [
                {
                    filename,
                    content: fs.createReadStream(`../avatar/Exports/${dirname}/${filename}`)
                }
            ]
        });
        res.status(200).json({ message: "success" });
        discordNotifySuccess(username, email);
    } catch (err) {
        res.status(500).json({ message: "Failed to send email, please contact us on discord" });
        console.log(err);
    }
}

async function getToken() {
    let url = "https://account.altvr.com/users/sign_in";
    let headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded",
    };
    return new Promise<string>(function (resolve, reject) {
        superagent.get(url).set(headers).end(function (err, response) {
            if (err) { reject }
            let $ = cheerio.load(response.text);
            resolve($("meta[name=csrf-token]").attr('content') as string);
        });
    });
}

function login(token: string) {
    let url = "https://account.altvr.com/users/sign_in";
    let headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded",
    };
    return new Promise<string[]>(function (resolve, reject) {
        superagent.post(url)
            .set(headers).send({
                'utf8': '✓',
                'user[tz_offset]': '-480',
                'user[remember_me]': '1',
                'authenticity_token': token,
                'user[email]': email,
                'user[password]': password,
            }).redirects(0).end(function (err, response) {
                if (err) { reject }
                let cookie: string[] = response.headers["set-cookie"];
                resolve(cookie);
            });
    });
}

async function get(url: string) {
    const headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        'Content-Type': 'application/x-www-form-urlencoded'
    };
    return new Promise<string>(function (resolve, reject) {
        superagent.get(url).set({ Cookie: cookie }).set(headers).end(function (err, response) {
            if (err) { reject }
            resolve(response.text);
        });
    });
}

async function getCustomization(
    username: string
) {
    if (cookie.length <= 0) {
        console.log('Logging in...');
        const token = await getToken();
        cookie = await login(token);
        console.log('Done.');
    }

    try {
        const user = JSON.parse(await get(`https://account.altvr.com/api/users/${username}`));
        const cid = user.users[0].avatar_customization_id;
        const customization = JSON.parse(await get(`https://account.altvr.com/api/avatar_customizations/${cid}`));
        return customization;
    } catch (e) {
        return null;
    }
}

function discordNotifyRequest(username: string, email: string, ip: string, extraThicc: boolean, autorig: boolean) {
    discordNotification
        .infoMessage()
        .addTitle('Avatar Request')
        .addField({ name: 'Email', value: email })
        .addField({ name: 'Username', value: username })
        .addField({ name: 'IP', value: ip, inline: false })
        .addField({ name: 'ExtraThicc', value: `${extraThicc}` })
        .addField({ name: 'Autorig', value: `${autorig}` })
        .sendMessage()
}

function discordNotifySuccess(username: string, email: string) {
    const url = `/avatar/api/preview?username=${encodeURIComponent(username)}&email=${encodeURIComponent(email)}`;
    discordNotification
        .sucessfulMessage()
        .addTitle('Avatar Request Done')
        .addDescription(`Avatar for ${username} by ${email} is done`)
        .addImage(`https://freemre.com/avatar/_next/image?url=${encodeURIComponent(url)}&w=256&q=75`)
        .sendMessage()
}
