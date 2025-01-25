import type { Metadata } from "next";
import React from "react";
import "./globals.css";
import { Lato, Raleway } from "next/font/google";
import NavBar from "@/components/navBar";

const raleway = Raleway({
    variable: "--font-raleway",
    weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
    subsets: ["latin"],
});

const lato = Lato({
    variable: "--font-lato",
    weight: ["100", "300", "400", "700", "900"],
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "SecureVision",
    description: "Secure Vision provides the ability to secure and retrieves the images.",
};

export default function RootLayout({children,}: Readonly<{ children: React.ReactNode; }>) {
    return (
        <html lang="en" className={`${raleway.variable} ${lato.variable} antialiased`}>
            <body className="bg-cyan-950 font-lato">
                <NavBar />
                {children}
            </body>
        </html>
    );
}
