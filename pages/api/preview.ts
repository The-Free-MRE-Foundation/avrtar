
import fs from 'fs';
import path from 'path';
import { NextApiRequest, NextApiResponse } from "next";

function writeLog(message: string) {
    fs.writeFileSync("log.txt",
        message,
        {
            encoding: "utf8",
            flag: "a+",
            mode: 0o666
        });
}

export default async function PreviewApi(
    req: NextApiRequest,
    res: NextApiResponse,
) {
    const { username, email } = req.query;

    const forwarded = req.headers["x-forwarded-for"] as string;
    const ip = forwarded ? forwarded.split(/, /)[0] : req.connection.remoteAddress

    const dirname = path.basename(encodeURIComponent(email as string));
    const filename = path.basename(encodeURIComponent(`${username}.png`));
    const filepath = `../avatar/Exports/${dirname}/${filename}`;

    console.log(`Preview request for ${filepath} from ${ip}`);
    writeLog('===============================================================================================\n');
    writeLog(`Preview request for ${filepath} from ${ip}\n`);
    const imageBuffer = fs.readFileSync(filepath);
    res.setHeader("Content-Type", "image/png");
    return res.status(200).send(imageBuffer);
}