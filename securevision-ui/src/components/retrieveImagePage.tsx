"use client";
import React, { useState, useCallback, useEffect } from "react";
import Image from "next/image";
import { IconUpload, IconCommand, IconPhoto, IconX, IconTrashX, IconFile, IconDownload } from "@tabler/icons-react";
import { motion, AnimatePresence } from "framer-motion";
import JSZip from "jszip";

interface UploadedFiles {
    share1: File | null;
    share2: File | null;
    recoveryData: File | null;
}

interface FilePreviews {
    share1: string | null;
    share2: string | null;
}

const ACCEPTED_TYPES = [
    "application/zip",
    "image/png",
    ".npy",
    "application/x-npy",
    "application/octet-stream", // For .npy files
];

const initialUploadedFiles: UploadedFiles = {
    share1: null,
    share2: null,
    recoveryData: null
};

const initialPreviews: FilePreviews = {
    share1: null,
    share2: null
};

export default function RetrieveImagePage() {
    const [dragActive, setDragActive] = useState<boolean>(false);
    const [isProcessing, setIsProcessing] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [retrievedImage, setRetrievedImage] = useState<string | null>(null);
    const [uploadMode, setUploadMode] = useState<"zip" | "individual" | null>(null);
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFiles>(initialUploadedFiles);
    const [previews, setPreviews] = useState<FilePreviews>(initialPreviews);
    const [zipFile, setZipFile] = useState<File | null>(null);

    const removeFile = (type: keyof UploadedFiles) => {
        if (type === "share1" || type === "share2") {
            if (previews[type]) {
                URL.revokeObjectURL(previews[type]!);
                setPreviews(prev => ({ ...prev, [type]: null }));
            }
        }

        setUploadedFiles(prev => ({ ...prev, [type]: null }));

        if (areAllFilesRemoved()) {
            setUploadMode(null);
            setError(null);
            setZipFile(null);
        }
    };

    const areAllFilesRemoved = () => {
        return Object.values(uploadedFiles).every(file => file === null);
    };

    const createZipFromFiles = async () => {
        const zip = new JSZip();

        if (!uploadedFiles.share1 || !uploadedFiles.share2 || !uploadedFiles.recoveryData) {
            throw new Error("Missing required files");
        }

        zip.file("share1.png", uploadedFiles.share1);
        zip.file("share2.png", uploadedFiles.share2);
        zip.file("recovery_data.npy", uploadedFiles.recoveryData);

        const zipBlob = await zip.generateAsync({ type: "blob" });
        return new File([zipBlob], "encrypted_package.zip", { type: "application/zip" });
    };

    const handleFile = async (files: FileList | null) => {
        if (!files) return;
        setError(null);

        // Handle ZIP file upload
        if (files[0]?.type === "application/zip") {
            if (uploadMode === "individual" && !areAllFilesRemoved()) {
                setError("Please remove existing files before uploading a ZIP file");
                return;
            }

            // In the ZIP handling section of handleFile function
            // In the ZIP handling section of handleFile function
            try {
                const zip = await JSZip.loadAsync(files[0]);
                const zipContents = Object.keys(zip.files);

                const hasShare1 = zipContents.includes("share1.png");
                const hasShare2 = zipContents.includes("share2.png");
                const hasRecovery = zipContents.includes("recovery_data.npy");

                if (!hasShare1 || !hasShare2 || !hasRecovery) {
                    setError("ZIP file must contain share1.png, share2.png, and recovery_data.npy");
                    return;
                }

                // Create blobs from the zip contents
                const share1Data = await zip.file("share1.png")?.async("blob");
                const share2Data = await zip.file("share2.png")?.async("blob");
                const recoveryData = await zip.file("recovery_data.npy")?.async("blob");

                if (share1Data && share2Data && recoveryData) {
                    setUploadMode("zip");
                    setZipFile(files[0]);
                    setUploadedFiles({
                        share1: new File([share1Data], "share1.png", { type: "image/png" }),
                        share2: new File([share2Data], "share2.png", { type: "image/png" }),
                        recoveryData: new File([recoveryData], "recovery_data.npy", { type: "application/octet-stream" })
                    });
                    setPreviews({
                        share1: URL.createObjectURL(share1Data),
                        share2: URL.createObjectURL(share2Data)
                    });
                }
            } catch (err) {
                setError("Error processing ZIP file");
                console.error(err);
            }
            return;
        }

        // Handle individual file uploads
        if (uploadMode === "zip" && !areAllFilesRemoved()) {
            setError("Please remove ZIP contents before uploading individual files");
            return;
        }

        setUploadMode("individual");

        Array.from(files).forEach(file => {
            if (file.type === "image/png") {
                if (!uploadedFiles.share1) {
                    setUploadedFiles(prev => ({ ...prev, share1: file }));
                    setPreviews(prev => ({
                        ...prev,
                        share1: URL.createObjectURL(file)
                    }));
                } else if (!uploadedFiles.share2) {
                    setUploadedFiles(prev => ({ ...prev, share2: file }));
                    setPreviews(prev => ({
                        ...prev,
                        share2: URL.createObjectURL(file)
                    }));
                }
            } else if (file.name.endsWith(".npy")) {
                setUploadedFiles(prev => ({ ...prev, recoveryData: file }));
            }
        });
    };

    const handleDrag = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        handleFile(e.dataTransfer.files);
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        handleFile(e.target.files);
    };

    const processImage = async () => {
        try {
            setIsProcessing(true);
            setError(null);

            let zipToSend: File;
            if (uploadMode === "zip" && zipFile) {
                zipToSend = zipFile;
            } else if (uploadMode === "individual") {
                zipToSend = await createZipFromFiles();
            } else {
                throw new Error("No valid files to process");
            }

            const formData = new FormData();
            formData.append("encrypted_package", zipToSend);

            const response = await fetch("http://127.0.0.1:8000/api/v1/decrypt", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Failed to process image");
            }

            const imageBlob = await response.blob();
            const imageUrl = URL.createObjectURL(imageBlob);
            setRetrievedImage(imageUrl);

        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
            setIsProcessing(false);
        }
    };

    const downloadImage = () => {
        if (!retrievedImage) return;

        const link = document.createElement("a");
        link.href = retrievedImage;
        link.download = "retrieved_image.png";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    useEffect(() => {
        const handlePaste = (e: ClipboardEvent) => {
            const items = e.clipboardData?.items;
            if (items) {
                const files: File[] = [];
                for (const item of items) {
                    if (item.type.includes("image")) {
                        const file = item.getAsFile();
                        if (file) files.push(file);
                    }
                }
                if (files.length > 0) {
                    handleFile(files as unknown as FileList);
                }
            }
        };

        window.addEventListener("paste", handlePaste);
        return () => window.removeEventListener("paste", handlePaste);
    }, []);

    // Clean up URLs on unmount
    useEffect(() => {
        return () => {
            if (retrievedImage) URL.revokeObjectURL(retrievedImage);
            Object.values(previews).forEach(preview => {
                if (preview) URL.revokeObjectURL(preview);
            });
        };
    }, [retrievedImage, previews]);

    const canRetrieve = uploadMode === "zip" ? zipFile !== null :
        (uploadedFiles.share1 && uploadedFiles.share2 && uploadedFiles.recoveryData);
    const isRetrieved = retrievedImage !== null;
    const hasAnyFile = uploadedFiles.share1 || uploadedFiles.share2 || uploadedFiles.recoveryData || zipFile !== null;

    const renderUploadArea = () => {
        if (hasAnyFile) {
            return (
                <div className="w-full h-full flex flex-col gap-4 p-4">
                    <div className="flex flex-row gap-4 flex-1">
                        {/* Share 1 Preview/Placeholder */}
                        <div className="w-1/2 relative">
                            {uploadedFiles.share1 && previews.share1 ? (
                                <>
                                    <Image
                                        src={previews.share1}
                                        alt="Share 1"
                                        fill
                                        className="object-contain rounded-xl"
                                    />
                                    <button
                                        onClick={(e) => {
                                            e.preventDefault();
                                            removeFile("share1");
                                        }}
                                        className="absolute bottom-2 right-2 p-2 rounded-full bg-red-500/50 hover:bg-red-500/80 transition-colors duration-200"
                                    >
                                        <IconTrashX className="w-5 h-5 text-white" />
                                    </button>
                                </>
                            ) : (
                                <div className="w-full h-full border-2 border-dashed border-teal-600/50 rounded-xl flex items-center justify-center">
                                    <span className="text-teal-400/70">Share 1</span>
                                </div>
                            )}
                        </div>

                        {/* Share 2 Preview/Placeholder */}
                        <div className="w-1/2 relative">
                            {uploadedFiles.share2 && previews.share2 ? (
                                <>
                                    <Image
                                        src={previews.share2}
                                        alt="Share 2"
                                        fill
                                        className="object-contain rounded-xl"
                                    />
                                    <button
                                        onClick={(e) => {
                                            e.preventDefault();
                                            removeFile("share2");
                                        }}
                                        className="absolute bottom-2 right-2 p-2 rounded-full bg-red-500/50 hover:bg-red-500/80 transition-colors duration-200"
                                    >
                                        <IconTrashX className="w-5 h-5 text-white" />
                                    </button>
                                </>
                            ) : (
                                <div className="w-full h-full border-2 border-dashed border-teal-600/50 rounded-xl flex items-center justify-center">
                                    <span className="text-teal-400/70">Share 2</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Recovery Data File/Placeholder */}
                    <div className="w-full">
                        {uploadedFiles.recoveryData ? (
                            <div className="w-full bg-teal-900/20 rounded-xl p-3 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <IconFile className="w-5 h-5 text-teal-400" />
                                    <span className="text-teal-100">recovery_data.npy</span>
                                </div>
                                <button
                                    onClick={(e) => {
                                        e.preventDefault();
                                        removeFile("recoveryData");
                                    }}
                                    className="p-1.5 rounded-full hover:bg-red-500/20 transition-colors duration-200"
                                >
                                    <IconX className="w-4 h-4 text-red-400" />
                                </button>
                            </div>
                        ) : (
                            <div className="w-full border-2 border-dashed border-teal-600/50 rounded-xl p-3 flex items-center justify-center">
                                <span className="text-teal-400/70">Recovery Data (.npy)</span>
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        return (
            <div className="flex flex-col items-center space-y-4 p-4">
                <IconUpload className="w-12 h-12 text-teal-500" />
                <div className="text-center space-y-0.5">
                    <div className="relative cursor-pointer font-lato rounded-md font-semibold text-teal-400/70 focus-within:outline-none focus-within:ring-2 focus-within:ring-teal-400/70 focus-within:ring-offset-2 hover:text-teal-500">
                        Choose files <span className="text-teal-50">or drag & drop</span>
                    </div>
                    <div className="flex items-center justify-center space-x-1 text-teal-400 text-md font-lato">
                        <IconCommand className="w-4 h-4" />
                        <span>+</span>
                        <span>V</span>
                        <span className="text-teal-400/70">to paste</span>
                    </div>
                    <p className="text-sm text-white/70 mt-2 font-lato">
                        Upload a ZIP file or individual share images (.PNG) and recovery data (.NPY)
                    </p>
                </div>
            </div>
        );
    };

    return (
        <div
            className="min-h-[calc(100vh-4rem)] bg-cyan-950 px-3 md:px-0"
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
        >
            <div className="max-w-4xl mx-auto pt-10 min-[400px]:pt-20 flex flex-col items-center h-[calc(100vh-5rem)]">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-teal-50 text-2xl sm:text-3xl md:text-4xl font-raleway mb-8"
                >
                    {isRetrieved ? "Image is Retrieved" : "Start Retrieving the Image"}
                </motion.h1>

                {/* Content Container */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="w-full flex flex-col lg:flex-row justify-center gap-6 pt-4"
                >
                    {/* Upload Area Container */}
                    <motion.div
                        initial={{ x: 0, y: 0 }}
                        animate={{
                            x: isRetrieved ? window.innerWidth >= 1024 ? "-10%" : 0 : 0,
                            y: isRetrieved ? window.innerWidth >= 1024 ? 0 : 0 : 0
                        }}
                        transition={{ type: "spring", stiffness: 100, damping: 20 }}
                        className="w-full lg:w-1/2"
                    >
                        <label
                            className={`
                                w-full aspect-video flex flex-col items-center justify-center
                                border-2 border-dashed rounded-2xl
                                ${hasAnyFile ? "border-teal-600" : "border-teal-600/50"}
                                ${hasAnyFile ? "bg-teal-900/20" : "bg-teal-900/10"}
                                transition-colors duration-200 cursor-pointer
                                hover:border-teal-500 hover:bg-teal-900/30
                                relative
                            `}
                        >
                            <input
                                type="file"
                                className="hidden"
                                accept={ACCEPTED_TYPES.join(",")}
                                onChange={handleChange}
                                multiple
                            />

                            {renderUploadArea()}

                            {dragActive && (
                                <div className="absolute inset-0 bg-teal-900/90 backdrop-blur-sm rounded-2xl flex items-center justify-center">
                                    <IconPhoto className="absolute top-1/3 left-8 w-8 h-8 text-teal-400/50 rotate-[-15deg]" />
                                    <IconPhoto className="absolute bottom-1/3 right-8 w-8 h-8 text-teal-400/50 rotate-[15deg]" />
                                    <div className="text-teal-50 text-xl font-raleway">
                                        Drop your files here to Retrieve
                                    </div>
                                </div>
                            )}
                        </label>
                    </motion.div>

                    {/* Retrieved Image Container */}
                    <AnimatePresence>
                        {isRetrieved && (
                            <motion.div
                                initial={{
                                    opacity: 0,
                                    x: window.innerWidth >= 1024 ? "10%" : 0,
                                    y: window.innerWidth >= 1024 ? 0 : 20
                                }}
                                animate={{
                                    opacity: 1,
                                    x: 0,
                                    y: 0
                                }}
                                transition={{ duration: 0.5, delay: 0.2 }}
                                className="w-full lg:w-1/2"
                            >
                                <div className="border-2 border-dashed border-teal-600 rounded-2xl bg-teal-900/20 aspect-video p-4 relative">
                                    <div className="relative w-full h-full rounded-lg overflow-hidden">
                                        <Image
                                            src={retrievedImage}
                                            alt="Retrieved Image"
                                            fill
                                            className="object-contain rounded-lg"
                                        />
                                    </div>

                                    {/* Download Button */}
                                    <div className="absolute bottom-3 right-3">
                                        <button
                                            onClick={downloadImage}
                                            className="p-2 rounded-full bg-emerald-500/50 hover:bg-emerald-500/80 transition-colors duration-200"
                                            title="Download Retrieved Image"
                                        >
                                            <IconDownload className="w-6 h-6 text-emerald-500 hover:text-emerald-800" />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>

                {/* Retrieve Button */}
                {!isRetrieved && (
                    <motion.button
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.4 }}
                        onClick={processImage}
                        disabled={!canRetrieve || isProcessing}
                        className={`
                            mt-6 px-6 py-3 rounded-2xl font-lato font-medium text-base md:text-lg
                            ${canRetrieve
                        ? isProcessing
                            ? "bg-teal-800 text-teal-400 cursor-not-allowed"
                            : "bg-teal-600 hover:bg-teal-500 text-white cursor-pointer"
                        : "bg-teal-800 text-teal-400 cursor-not-allowed"
                    }
                            transition-colors duration-200
                        `}
                    >
                        {isProcessing ? "Retrieving the Image..." : "Retrieve Image"}
                    </motion.button>
                )}

                {error && (
                    <div className="mt-4 text-red-400 text-sm font-lato">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
}
