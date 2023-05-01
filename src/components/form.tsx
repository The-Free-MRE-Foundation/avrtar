import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { FiMail, FiUser } from "react-icons/fi";
import Image from 'next/image'

const formSchema = z.object({
  username: z.string().min(1, { message: "Full name is required" }),
  email: z.string().min(1, { message: "Email is required" }).email({
    message: "Must be a valid email",
  }),
  extraThicc: z.boolean().default(false),
  autorig: z.boolean().default(false),
});

type FormData = z.infer<typeof formSchema>;

export default function Form() {
  const [result, setResult] = useState<string>();
  const [resultColor, setResultColor] = useState<string>();
  const [preview, setPreview] = useState<string>();
  const [showModal, setShowModal] = React.useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isSubmitSuccessful },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    // defaultValues: {
    //   username: "illuminati_official",
    //   email: "luminosity@freemre.com",
    // },
  });
  const processForm = async (data: FormData) => {
    const config = {
      method: "post",
      url: "/avatar/api/form",
      headers: {
        "Content-Type": "application/json",
      },
      data: data,
    };
    try {
      const response = await axios(config);
      if (response.status === 200) {
        // Handle success. You can change the message to whatever you want.
        setResult(
          `Your avatar has been sent to ${data.email}`
        );
        setResultColor("text-green-500");
        setPreview(`/avatar/api/preview?username=${encodeURIComponent(data.username)}&email=${encodeURIComponent(data.email)}`)
        // Reset the form after successful submission
        reset();
      }
    } catch (err: any) {
      // Handle errors. You can change the message to whatever you want.
      setResult(err.response.data.message);
      setResultColor("text-red-500");
      setPreview(undefined)
    }
  };

  return (
    <form className="w-full" onSubmit={handleSubmit(processForm)} noValidate>
      <div className="mb-4">
        <div className="relative">
          {errors.email?.message ? (
            <FiMail className="w-6 h-6 absolute top-1/2 -translate-y-1/2 left-2 border-r pr-2 text-red-500" />
          ) : (
            <FiMail className="w-6 h-6 absolute top-1/2 -translate-y-1/2 left-2 border-r pr-2" />
          )}
          <input
            className={`shadow appearance-none outline-none border rounded w-full py-2 pl-10 text-gray-700  leading-tight duration-300
          ${errors.email?.message && "shadow-[0_0_0_2px] shadow-red-500"}
          `}
            type="email"
            placeholder="Email to Receive Your Avatar with"
            {...register("email")}
          />
        </div>
        {errors.email?.message && (
          <div className="text-red-500 text-xs mt-1">
            {errors.email?.message}
          </div>
        )}
      </div>
      <div className="mb-4">
        <div className="relative">
          {errors.username?.message ? (
            <FiUser className="w-6 h-6 absolute top-1/2 -translate-y-1/2 left-2 border-r pr-2 text-red-500" />
          ) : (
            <FiUser className="w-6 h-6 absolute top-1/2 -translate-y-1/2 left-2 border-r pr-2" />
          )}
          <input
            className={`shadow appearance-none outline-none border rounded w-full py-2 pl-10 text-gray-700 leading-tight duration-300
          ${errors.username?.message && "shadow-[0_0_0_2px] shadow-red-500"}
          `}
            type="text"
            placeholder="Altspace Username (not Display Name)"
            {...register("username")}
          />
        </div>
        {errors.username?.message && (
          <div className="text-red-500 text-xs mt-1">
            {errors.username?.message}
          </div>
        )}
      </div>
      <div className="mb-4 inline-block">
        <div className="relative">
          <input
            type="checkbox"
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
            {...register("extraThicc")}
          />
          <label className="ml-2 text-sm font-medium text-black-900 dark:text-gray-300">Extra Thicc?</label>
        </div>
        <div className="relative">
          <input
            type="checkbox"
            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
            {...register("autorig")}
          />
          <label className="ml-2 text-sm font-medium text-black-900 dark:text-gray-300">Autorig for Unity?</label>
          &nbsp; <a href="https://discord.com/channels/996556066831737013/1064139468241649714" className="font-medium text-blue-600 dark:text-blue-500 hover:underline">(Tutorial)</a>
        </div>
      </div>
      <div className="flex gap-10 items-center justify-between">
        <button
          className={`${isSubmitting
            ? "opacity-50 cursor-not-allowed"
            : "opacity-100 cursor-pointer"
            } bg-black hover:bg-gray-700 text-white font-bold py-2 px-6 rounded focus:outline-none focus:shadow-outline duration-300`}
          type="submit"
          disabled={isSubmitting}
          onClick={handleSubmit(processForm)}
        >
          {isSubmitting ? "Processing... This could take up to 20s" : "Get My Avatar By Email Now"}
        </button>
        <label className="ml-2 text-sm font-medium text-black-900 dark:text-gray-300">By submitting you agree to our <a onClick={()=>setShowModal(true)} className="underline text-blue-600 hover:text-blue-800 visited:text-purple-600">terms of use</a></label>
        {isSubmitSuccessful && (
          <div className={`text-right ${resultColor}`}>{result}</div>
        )}
      </div>
      {isSubmitSuccessful && preview && (
        <div className="mb-4">
          <div
            className="relative"
            style={{ display: "flex", justifyContent: "center", alignItems: "center" }}
          >
            <Image
              src={preview}
              alt="Preview of you avatar"
              width={256}
              height={256}
            />
          </div>
        </div>
      )}
      {showModal ? (
        <>
          <div
            className="justify-center items-center flex overflow-x-hidden overflow-y-auto fixed inset-0 z-50 outline-none focus:outline-none"
          >
            <div className="relative w-auto my-6 mx-auto max-w-3xl">
              {/*content*/}
              <div className="border-0 rounded-lg shadow-lg relative flex flex-col w-full bg-white outline-none focus:outline-none">
                {/*header*/}
                <div className="flex items-start justify-between p-5 border-b border-solid border-slate-200 rounded-t">
                  <h3 className="text-3xl font-semibold">
                    Terms of Use
                  </h3>
                  <button
                    className="p-1 ml-auto bg-transparent border-0 text-black opacity-5 float-right text-3xl leading-none font-semibold outline-none focus:outline-none"
                    onClick={() => setShowModal(false)}
                  >
                    <span className="bg-transparent text-black opacity-5 h-6 w-6 text-2xl block outline-none focus:outline-none">
                      ×
                    </span>
                  </button>
                </div>
                {/*body*/}
                <div className="relative p-6 flex-auto">
                  <p className="my-4 text-slate-500 text-lg leading-relaxed">
                    By downloading you agree to not use for profit, not sell as a service,
                    and not in any form profit from any method using this model.
                    By agreeing, you agree that you will only use the model for &quot;Personal use&quot;
                    and not use in any future for-profit ideas.
                    Anyone caught doing so will be banned permanently from all future projects including updates on this one.
                  </p>
                </div>
                {/*footer*/}
                <div className="flex items-center justify-end p-6 border-t border-solid border-slate-200 rounded-b">
                  <button
                    className="bg-emerald-500 text-white active:bg-emerald-600 font-bold uppercase text-sm px-6 py-3 rounded shadow hover:shadow-lg outline-none focus:outline-none mr-1 mb-1 ease-linear transition-all duration-150"
                    type="button"
                    onClick={() => setShowModal(false)}
                  >
                    Ok
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div className="opacity-25 fixed inset-0 z-40 bg-black"></div>
        </>
      ) : null}
    </form>
  );
}
