"use client";
import React from "react";
import {motion} from "framer-motion";
import {Lock, LockOpen} from "lucide-react";
import Link from "next/link";

export default function HomePage () {
    return (
        <div className="h-screen w-screen bg-cyan-950 overflow-hidden">
            {/* Main Content */}
            <div className="h-full w-full flex flex-col items-center pt-16 md:pt-20 px-4">
                {/* Welcome Text */}
                <motion.div
                    initial={{opacity: 0, y: -20}}
                    animate={{opacity: 1, y: 0}}
                    transition={{duration: 0.6}}
                    className="mb-12"
                >
                    <h1 className="text-cyan-50 text-3xl md:text-4xl font-raleway text-center">
                        Hello, User
                    </h1>
                    <p className="text-cyan-400/70 text-lg md:text-xl font-lato text-center mt-2">
                        What would you like to do today?
                    </p>
                </motion.div>

                {/* Action Cards */}
                <motion.div
                    initial={{opacity: 0, y: 20}}
                    animate={{opacity: 1, y: 0}}
                    transition={{duration: 0.6, delay: 0.2}}
                    className="w-full max-w-4xl px-4"
                >
                    <div className="flex flex-col md:flex-row gap-6 w-full">
                        {/* Secure Image Card */}
                        <Link href="/secure-image" className="w-full md:w-1/2">
                            <motion.div
                                whileHover={{scale: 1.02}}
                                className="w-full aspect-video cursor-pointer group"
                            >
                                <div className="w-full h-full rounded-2xl border-2 border-dashed border-cyan-600/50 bg-cyan-900/10 p-6
                  flex flex-col items-center justify-center gap-4
                  transition-colors duration-200
                  group-hover:border-cyan-500 group-hover:bg-cyan-900/30">

                                    <motion.div
                                        whileHover={{rotate: [0, -10, 0]}}
                                        transition={{duration: 0.5}}
                                        className="p-4 rounded-full bg-cyan-900/50 group-hover:bg-cyan-800/50"
                                    >
                                        <Lock className="w-16 h-16 text-cyan-400 group-hover:text-cyan-300"/>
                                    </motion.div>

                                    <div className="text-center">
                                        <h3 className="text-2xl font-raleway text-cyan-50 mb-2">
                                            Secure an Image
                                        </h3>
                                        <p className="text-cyan-400/70 font-lato">
                                            Encrypt, Protect and Secure your Image
                                        </p>
                                    </div>
                                </div>
                            </motion.div>
                        </Link>

                        {/* Retrieve Image Card */}
                        <Link href="/retrieve-image" className="w-full md:w-1/2">
                            <motion.div
                                whileHover={{scale: 1.02}}
                                className="w-full aspect-video cursor-pointer group"
                            >
                                <div className="w-full h-full rounded-2xl border-2 border-dashed border-teal-600/50 bg-teal-900/10 p-6
                  flex flex-col items-center justify-center gap-4
                  transition-colors duration-200
                  group-hover:border-teal-500 group-hover:bg-teal-900/30">

                                    <motion.div
                                        whileHover={{rotate: [0, 10, 0]}}
                                        transition={{duration: 0.5}}
                                        className="p-4 rounded-full bg-teal-900/50 group-hover:bg-teal-800/50"
                                    >
                                        <LockOpen className="w-16 h-16 text-teal-400 group-hover:text-teal-300"/>
                                    </motion.div>

                                    <div className="text-center">
                                        <h3 className="text-2xl font-raleway text-teal-50 mb-2">
                                            Retrieve an Image
                                        </h3>
                                        <p className="text-teal-400/70 font-lato">
                                            Decrypt, Recover and Restore your Image
                                        </p>
                                    </div>
                                </div>
                            </motion.div>
                        </Link>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};
