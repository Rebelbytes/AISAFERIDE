import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Camera, AlertCircle, Check } from "lucide-react";
import api from "../utils/api";

export default function LiveDetection() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [annotatedImage, setAnnotatedImage] = useState(null);
  const [violationTypes, setViolationTypes] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [vehicleType, setVehicleType] = useState("2 wheeler");
  const [violationCategory, setViolationCategory] = useState("general");
  const [error, setError] = useState(null);

  useEffect(() => {
    let stream = null;
    let animationId = null;
    let frameCount = 0;
    let processInterval = null;

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'environment' // Use back camera if available
          } 
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play();
          setIsCameraOn(true);
          setError(null);
        }
      } catch (err) {
        setError("Error accessing camera: " + err.message);
        console.error("Camera error:", err);
      }
    };

    const processFrame = () => {
      if (!isCameraOn || !videoRef.current || !canvasRef.current || videoRef.current.videoWidth === 0) {
        animationId = requestAnimationFrame(processFrame);
        return;
      }

      frameCount++;
      
      // Draw frame to canvas for processing
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      ctx.drawImage(videoRef.current, 0, 0);

      // Process every 60 frames (~2 FPS for better performance, reduce lag)
      if (frameCount % 60 === 0) {
        const frameData = canvas.toDataURL("image/jpeg", 0.7); // Lower quality for faster transmission

        setIsProcessing(true);
        api.post("/live-detect/", {
          vehicle_type: vehicleType,
          violation_category: violationCategory,
          image_base64: frameData
        })
        .then(response => {
          setAnnotatedImage(response.data.annotated_image_base64);
          setViolationTypes(response.data.violation_types || []);
          setError(null);
        })
        .catch(err => {
          console.error("Live detection error:", err);
          setError("Detection error: " + (err.response?.data?.error || err.message));
        })
        .finally(() => setIsProcessing(false));
      }

      animationId = requestAnimationFrame(processFrame);
    };

    if (isCameraOn) {
      // Start processing after video is ready
      const startProcessing = () => {
        frameCount = 0;
        processFrame();
      };

      videoRef.current.addEventListener("loadedmetadata", startProcessing);
      videoRef.current.addEventListener("canplay", startProcessing);

      // Also start a timer-based processing for consistency
      processInterval = setInterval(() => {
        if (isCameraOn && videoRef.current && videoRef.current.readyState >= 2) {
          const canvas = canvasRef.current;
          const ctx = canvas.getContext("2d");
          canvas.width = videoRef.current.videoWidth;
          canvas.height = videoRef.current.videoHeight;
          ctx.drawImage(videoRef.current, 0, 0);
          const frameData = canvas.toDataURL("image/jpeg", 0.7);

          setIsProcessing(true);
          api.post("/live-detect/", {
            vehicle_type: vehicleType,
            violation_category: violationCategory,
            image_base64: frameData
          })
          .then(response => {
            setAnnotatedImage(response.data.annotated_image_base64);
            setViolationTypes(response.data.violation_types || []);
            setError(null);
          })
          .catch(err => {
            console.error("Live detection error:", err);
            setError("Detection error: " + (err.response?.data?.error || err.message));
          })
          .finally(() => setIsProcessing(false));
        }
      }, 2000); // Process every 2 seconds to reduce lag
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      if (processInterval) {
        clearInterval(processInterval);
      }
    };
  }, [isCameraOn, vehicleType, violationCategory]);

  const handleStartLive = () => {
    setIsCameraOn(true);
  };

  const handleStopLive = () => {
    setIsCameraOn(false);
    setAnnotatedImage(null);
    setViolationTypes([]);
  };

  const handleBack = () => {
    navigate("/");
  };

  const handleSaveViolation = (violation) => {
    if (!annotatedImage) {
      setError("No annotated image available to save violation.");
      return;
    }

    api.post("/save-violation/", {
      annotated_image_base64: annotatedImage,
      violation: violation
    })
    .then(response => {
      alert("Violation saved successfully!");
      setError(null);
    })
    .catch(err => {
      console.error("Save violation error:", err);
      setError("Save error: " + (err.response?.data?.error || err.message));
    });
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-8">
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="max-w-6xl mx-auto"
      >
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <ArrowLeft className="w-5 h-5" />
            Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-center flex-1">Live Detection</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Camera Feed */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Camera className="w-5 h-5" />
              Live Camera Feed
            </h2>
            <div className="relative">
              {isCameraOn ? (
                <>
                  <video
                    ref={videoRef}
                    autoPlay
                    muted
                    playsInline
                    className="w-full rounded max-h-96 object-contain"
                  />
                  {isProcessing && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded">
                      <div className="text-white flex items-center gap-2">
                        Processing...
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="w-full h-96 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center">
                  <Camera className="w-16 h-16 text-gray-400" />
                </div>
              )}
            </div>
            <div className="flex gap-4 mt-4">
              <button
                onClick={handleStartLive}
                disabled={isCameraOn}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg flex items-center justify-center gap-2"
              >
                <Camera className="w-4 h-4" />
                Start Live
              </button>
              <button
                onClick={handleStopLive}
                disabled={!isCameraOn}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white rounded-lg flex items-center justify-center gap-2"
              >
                <Check className="w-4 h-4" />
                Stop
              </button>
            </div>
          </div>

          {/* Annotated Feed & Violations */}
          <div className="space-y-4">
            <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
              <h2 className="text-lg font-semibold mb-4">Annotated Detection</h2>
              {annotatedImage ? (
                <img
                  src={annotatedImage}
                  alt="Annotated Live"
                  className="w-full rounded max-h-96 object-contain border-2 border-blue-500"
                />
              ) : (
                <div className="w-full h-96 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center">
                  <p className="text-gray-500">No detection yet. Start live feed.</p>
                </div>
              )}
            </div>

            {violationTypes.length > 0 && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-500" />
                  Live Violations
                </h2>
                <ul className="space-y-2">
                  {violationTypes.map((violation, index) => (
                    <li
                      key={index}
                      className="flex justify-between items-center p-3 bg-red-50 dark:bg-red-900/20 rounded border-l-4 border-red-500"
                    >
                      <span className="font-medium">{violation.type}</span>
                      <span className="text-sm text-gray-600 dark:text-gray-300">
                        Confidence: {(violation.confidence * 100).toFixed(1)}%
                      </span>
                      <button
                        onClick={() => handleSaveViolation(violation)}
                        className="ml-4 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded"
                      >
                        Save
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded border-l-4 border-red-500">
                <p className="text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* Vehicle Type Selector */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
          <label className="block text-sm font-medium mb-2">Vehicle Type</label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="vehicleType"
                value="2 wheeler"
                checked={vehicleType === "2 wheeler"}
                onChange={(e) => setVehicleType(e.target.value)}
                className="mr-2"
                disabled={isCameraOn}
              />
              2 Wheeler
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="vehicleType"
                value="4 wheeler"
                checked={vehicleType === "4 wheeler"}
                onChange={(e) => setVehicleType(e.target.value)}
                className="mr-2"
                disabled={isCameraOn}
              />
              4 Wheeler
            </label>
          </div>
        </div>

        {/* Violation Category Selector */}
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
          <label className="block text-sm font-medium mb-2">Violation Category</label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="violationCategory"
                value="general"
                checked={violationCategory === "general"}
                onChange={(e) => setViolationCategory(e.target.value)}
                className="mr-2"
                disabled={isCameraOn}
              />
              General
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="violationCategory"
                value="red_light"
                checked={violationCategory === "red_light"}
                onChange={(e) => setViolationCategory(e.target.value)}
                className="mr-2"
                disabled={isCameraOn}
              />
              Red Light
            </label>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
