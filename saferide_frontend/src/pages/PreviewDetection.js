import { useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Check, AlertCircle, Save } from "lucide-react";
import api from "../utils/api";

export default function PreviewDetection() {
  const location = useLocation();
  const navigate = useNavigate();
  const { annotated_media, violation_types, violation_images, originalFile } = location.state || {};
  const [originalPreview, setOriginalPreview] = useState(null);
  const [savedViolations, setSavedViolations] = useState([]);
  const [saving, setSaving] = useState({});

  useEffect(() => {
    if (originalFile && originalFile.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => setOriginalPreview(e.target.result);
      reader.readAsDataURL(originalFile);
    }
  }, [originalFile]);

  const handleSave = async (violation, index) => {
    if (originalFile && originalFile.type.startsWith('video/')) {
      alert("Selective saving for videos is not supported yet. Please save the full annotated video if needed.");
      return;
    }

    if (!annotated_media || annotated_media.length === 0) {
      alert("No annotated media available to crop from.");
      return;
    }

    setSaving(prev => ({ ...prev, [index]: true }));

    try {
      const response = await api.post('/save-violation/', {
        annotated_image_url: annotated_media[0],
        violation: violation
      });

      setSavedViolations(prev => [...prev, { ...violation, savedUrl: response.data.image_url }]);
      alert(`Violation saved successfully: ${response.data.image_url}`);
    } catch (error) {
      console.error("Error saving violation:", error);
      alert("Failed to save violation. Please try again.");
    } finally {
      setSaving(prev => ({ ...prev, [index]: false }));
    }
  };

  const handleBack = () => {
    navigate("/");
  };

  const handleProceed = () => {
    // Navigate to detection page with full data for full report
    navigate("/detection", { state: { data: { annotated_media, violation_types, violation_images } } });
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-8">
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
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
          <h1 className="text-3xl font-bold text-center flex-1">Detection Preview</h1>
        </div>

        {violation_types && violation_types.length > 0 ? (
          <>
            {/* Original vs Annotated Preview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
              {/* Original Image/Video */}
              {originalPreview && (
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
                  <h2 className="text-lg font-semibold mb-4">Original Media</h2>
                  {originalFile && originalFile.type.startsWith('video/') ? (
                    <video src={originalPreview} controls className="w-full h-auto rounded max-h-96 object-contain">
                      Your browser does not support the video tag.
                    </video>
                  ) : (
                    <img src={originalPreview} alt="Original" className="w-full h-auto rounded max-h-96 object-contain" />
                  )}
                </div>
              )}
              {/* Annotated Media */}
              {annotated_media && annotated_media.length > 0 && (
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg">
                  <h2 className="text-lg font-semibold mb-4">Annotated Detection (with Bounding Boxes)</h2>
                  {annotated_media[0].endsWith('.mp4') || annotated_media[0].endsWith('.avi') || annotated_media[0].endsWith('.mov') ? (
                    <video 
                      src={`http://127.0.0.1:8000${annotated_media[0]}`} 
                      autoPlay 
                      loop 
                      muted 
                      className="w-full h-auto rounded max-h-96 object-contain border-2 border-blue-500" 
                    >
                      Your browser does not support the video tag.
                    </video>
                  ) : (
                    <img 
                      src={`http://127.0.0.1:8000${annotated_media[0]}`} 
                      alt="Annotated" 
                      className="w-full h-auto rounded max-h-96 object-contain border-2 border-blue-500" 
                    />
                  )}
                </div>
              )}
            </div>

            {/* Violations List with Images */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg mb-8">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                Detected Violations
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {violation_types.map((violation, index) => (
                  <div key={index} className="p-3 bg-red-50 dark:bg-red-900/20 rounded border-l-4 border-red-500">
                    <div className="font-medium mb-2">{violation.type}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                      Confidence: {(violation.confidence * 100).toFixed(1)}%
                    </div>
                    {violation_images && violation_images.length > 0 && (
                      <img
                        src={`http://127.0.0.1:8000${violation_images[index] || violation_images[0]}`}
                        alt={`${violation.type} violation`}
                        className="w-full h-32 object-cover rounded border border-red-300"
                      />
                    )}
                    <button
                      onClick={() => handleSave(violation, index)}
                      disabled={saving[index]}
                      className="mt-2 w-full px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white text-sm rounded flex items-center justify-center gap-1"
                    >
                      <Save className="w-3 h-3" />
                      {saving[index] ? "Saving..." : "Save Violation"}
                    </button>
                    {savedViolations.some(sv => sv.type === violation.type && sv.confidence === violation.confidence) && (
                      <div className="mt-1 text-xs text-green-600">Saved</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* All Violation Images Grid */}
            {violation_images && violation_images.length > 0 && (
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg mb-8">
                <h2 className="text-xl font-bold mb-4">Violation Images</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {violation_images.map((imageUrl, index) => (
                    <div key={index} className="relative group">
                      <img 
                        src={`http://127.0.0.1:8000${imageUrl}`} 
                        alt={`Violation ${index + 1}`} 
                        className="w-full h-32 object-cover rounded border" 
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 rounded flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                        <span className="text-white text-sm">Violation Image {index + 1}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end gap-4">
              <button
                onClick={handleBack}
                className="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <button
                onClick={handleProceed}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center gap-2"
              >
                <Check className="w-4 h-4" />
                Proceed to Report
              </button>
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">No Violations Detected</h2>
            <p className="text-gray-500">The uploaded media does not show any violations.</p>
            {/* Still show annotated media even if no violations */}
            {annotated_media && annotated_media.length > 0 && (
              <div className="mt-8">
                <h3 className="text-lg font-semibold mb-4">Annotated Media (No Violations)</h3>
                {annotated_media[0].endsWith('.mp4') || annotated_media[0].endsWith('.avi') || annotated_media[0].endsWith('.mov') ? (
                  <video 
                    src={`http://127.0.0.1:8000${annotated_media[0]}`} 
                    autoPlay 
                    loop 
                    muted 
                    className="mx-auto rounded max-w-md" 
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <img 
                    src={`http://127.0.0.1:8000${annotated_media[0]}`} 
                    alt="Annotated" 
                    className="mx-auto rounded max-w-md max-h-96 object-contain" 
                  />
                )}
              </div>
            )}
            <button
              onClick={handleBack}
              className="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
            >
              Back to Dashboard
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
