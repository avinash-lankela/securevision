from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
import os
from zipfile import ZipFile
from datetime import datetime
from app.schemas.responses import APIResponse
from app.services.image_processor import encrypt_image, decrypt_image

# Create results directories if they don't exist
RESULTS_DIR = "results"
ENCRYPTION_DIR = os.path.join(RESULTS_DIR, "encryption")
DECRYPTION_DIR = os.path.join(RESULTS_DIR, "decryption")
os.makedirs(ENCRYPTION_DIR, exist_ok=True)
os.makedirs(DECRYPTION_DIR, exist_ok=True)

app = FastAPI(
    title="SecureVisionAPI",
    description="Image Security System API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=APIResponse)
async def root():
    return APIResponse(
        status="healthy",
        message="SecureVision API is running"
    )


@app.post("/api/v1/encrypt")
async def encrypt_image_endpoint(image: UploadFile):
    try:
        # Read and validate input image
        image_data = await image.read()
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None or img.shape != (256, 256, 3):
            raise HTTPException(
                status_code=400,
                detail="Invalid image. Please provide a 256x256 RGB image."
            )

        # Process image
        share1, share2, recovery_data = encrypt_image(img)

        # Create timestamped directory for this encryption
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = os.path.join(ENCRYPTION_DIR, timestamp)
        os.makedirs(result_dir, exist_ok=True)

        # Save individual files
        cv2.imwrite(os.path.join(result_dir, "share1.png"), share1)
        cv2.imwrite(os.path.join(result_dir, "share2.png"), share2)

        # Save recovery data
        recovery_data_combined = {
            'blue': {'R3': recovery_data['blue'][0], 'R4': recovery_data['blue'][1]},
            'green': {'R3': recovery_data['green'][0], 'R4': recovery_data['green'][1]},
            'red': {'R3': recovery_data['red'][0], 'R4': recovery_data['red'][1]}
        }
        np.save(os.path.join(result_dir, "recovery_data.npy"), recovery_data_combined)

        # Create ZIP file
        zip_path = os.path.join(result_dir, "encrypted_package.zip")
        with ZipFile(zip_path, 'w') as zipf:
            zipf.write(os.path.join(result_dir, "share1.png"), "share1.png")
            zipf.write(os.path.join(result_dir, "share2.png"), "share2.png")
            zipf.write(os.path.join(result_dir, "recovery_data.npy"), "recovery_data.npy")

        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f"encrypted_package_{timestamp}.zip"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/decrypt")
async def decrypt_image_endpoint(encrypted_package: UploadFile):
    try:
        if not encrypted_package.filename.endswith('.zip'):
            raise HTTPException(
                status_code=400,
                detail="Please provide a ZIP file containing shares and recovery data"
            )

        # Create timestamped directory for this decryption
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = os.path.join(DECRYPTION_DIR, timestamp)
        os.makedirs(result_dir, exist_ok=True)

        # Save and extract ZIP
        zip_content = await encrypted_package.read()
        zip_path = os.path.join(result_dir, "package.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_content)

        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(result_dir)

        # Read files
        share1 = cv2.imread(os.path.join(result_dir, "share1.png"))
        share2 = cv2.imread(os.path.join(result_dir, "share2.png"))
        recovery_data_combined = np.load(os.path.join(result_dir, "recovery_data.npy"), allow_pickle=True).item()

        # Reconstruct recovery_data
        recovery_data = {
            'blue': (recovery_data_combined['blue']['R3'], recovery_data_combined['blue']['R4']),
            'green': (recovery_data_combined['green']['R3'], recovery_data_combined['green']['R4']),
            'red': (recovery_data_combined['red']['R3'], recovery_data_combined['red']['R4'])
        }

        # Decrypt image
        decrypted_image = decrypt_image(share1, share2, recovery_data)

        # Save decrypted image
        decrypted_path = os.path.join(result_dir, "decrypted_image.png")
        cv2.imwrite(decrypted_path, decrypted_image)

        return FileResponse(
            decrypted_path,
            media_type="image/png",
            filename=f"decrypted_image_{timestamp}.png"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
