import Head from "next/head";
import Form from "../src/components/form";
import Link from "next/link";
import Image from "next/image";
import logoPic from '../public/freelogo.png'

export default function Home() {
  return (
    <>
      <nav style={{ position: "absolute", top: 0, width: "100%" }} className="bg-white border-gray-200 px-2 sm:px-4 py-2.5 rounded dark:bg-gray-900">
        <div className="container flex flex-wrap items-center justify-between mx-auto">
          <a href="https://freemre.com/" className="flex items-center">
            <Image src={logoPic} width={32} height={32} className="h-6 mr-3 sm:h-9" alt="Free MRE Logo" />
            <span className="self-center text-xl font-semibold whitespace-nowrap dark:text-white">Preserve My Avatars</span>
          </a>
          <div className="flex md:order-2">
            <p className="text-black font-medium rounded-lg text-sm px-5 py-2.5 text-center mr-3 md:mr-0 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">In <span style={{ color: "#e25555" }}>&#9829;</span>&nbsp; memory of Altspace</p>
          </div>
        </div>
      </nav>

      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <Head>
          <title>Preserve My Avatars</title>
          <link rel="icon" type="image/png" href="avatar/favicon.ico"></link>
        </Head>
        <div className="md:w-1/2 w-5/6 p-5 border mx-auto my-5 bg-slate-200 rounded-lg">
          <p className="mb-12">
            <span className="text-xl font-bold">
              What is this?
            </span>
            <br />
            This is a free app for helping Altspacers preserve their avatars.
            <br />
            <span className="text-xl font-bold">
              How to use it?
            </span>
            <br />
            Put in your Altspace username and email and the app will send you a 3D model of your avatar through email.
            <br />
            <span className="text-xl font-bold">
              Any restrictions?
            </span>
            <br />
            Each email can request up to 6 avatars.
            <br />
          </p>
          <Form />
        </div>
        <div style={{ position: "absolute", bottom: 0, width: "100%" }} className="bg-gray-100">
          <div className="container flex flex-wrap items-center justify-between mx-auto">
            <div className="flex items-center">
              Having trouble? ask us on &nbsp;
              <Link
                className="font-bold underline"
                href="https://freemre.com"
                target={"_blank"}
              >
                discord
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}