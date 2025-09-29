import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, AlertCircle } from "lucide-react";
import api from "../utils/api";

export default function Detection() {
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const data = location.state?.data || {};
  const annotatedMedia = data.annotated_media || [];
  const violationTypes = data.violation_types || [];

  const handleBack = () => {
    navigate("/");
  };

  const handleSaveViolation = async (violation) => {
    if (!annotatedMedia.length) {
      setError("No annotated media available to save violation.");
      return;
    }

    try {
      const response = await api.post('/save-violation/', {
        annotated_image_url: annotatedMedia[0],
        violation: violation
      });

      if (response.status === 201) {
        alert(`Violation saved successfully! Image URL: ${response.data.image_url}`);
      } else {
        setError("Failed to save violation.");
      }
    } catch (error) {
      console.error('Save violation error:', error);
      setError("Error saving violation: " + error.message);
    }
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
          <h1 className="text-3xl font-bold text-center flex-1">Detection Results</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Annotated Media */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
            <h2 className="text-lg font-semibold mb-4">Annotated Detection</h2>
            {annotatedMedia.length > 0 ? (
              annotatedMedia[0].endsWith('.mp4') || annotatedMedia[0].endsWith('.avi') || annotatedMedia[0].endsWith('.mov') ? (
                <video
                  src={`http://localhost:8000${annotatedMedia[0]}`}
                  controls
                  className="w-full rounded max-h-96 object-contain"
                />
              ) : (
                <img
                  src={`http://localhost:8000${annotatedMedia[0]}`}
                  alt="Annotated Detection"
                  className="w-full rounded max-h-96 object-contain border-2 border-blue-500"
                />
              )
            ) : (
              <div className="w-full h-96 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center">
                <p className="text-gray-500">No annotated media available.</p>
              </div>
            )}
          </div>

          {/* Violations */}
          <div className="space-y-4">
            {violationTypes.length > 0 && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-500" />
                  Detected Violations
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
      </motion.div>
    </div>
  );
}
