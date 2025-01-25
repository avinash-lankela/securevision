"use client";
import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { IconPhotoPlus, IconPhotoShield } from "@tabler/icons-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function NavBar() {
    const pathname = usePathname();
    const [showButton, setShowButton] = useState(false);

    useEffect(() => {
        setShowButton(["/secure-image", "/retrieve-image"].includes(pathname));
    }, [pathname]);

    return (
        <nav className="w-full bg-cyan-950 h-16">
            <div className="max-w-7xl mx-auto px-4 h-full">
                <div className="flex justify-between items-center h-full">
                    <Link href="/">
                        <motion.div
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6 }}
                            className="flex items-center space-x-2"
                        >
                            <IconPhotoShield className="text-cyan-50 h-8 w-8"/>
                            <span className="text-cyan-50 text-xl font-semibold font-raleway">
                                SecureVision
                            </span>
                        </motion.div>
                    </Link>

                    {showButton && (
                        <motion.button
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.2 }}
                            className="bg-teal-600 hover:bg-teal-500 transition-colors duration-200 text-white px-4 py-2 rounded-full flex items-center space-x-2 font-lato"
                        >
                            <IconPhotoPlus className="h-5 w-5"/>
                            <span className="hidden sm:inline sm:pl-1 sm:text-base font-medium">
                                New Conversion
                            </span>
                        </motion.button>
                    )}
                </div>
            </div>
        </nav>
    );
}
