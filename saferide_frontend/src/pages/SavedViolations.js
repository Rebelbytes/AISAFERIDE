import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Image as ImageIcon, Calendar, Folder, Download, ChevronDown, ChevronUp } from "lucide-react";
import api from "../utils/api";

export default function SavedViolations() {
  const navigate = useNavigate();
  const [violationsByDate, setViolationsByDate] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedFolders, setExpandedFolders] = useState({});

  useEffect(() => {
    fetchSavedViolations();
  }, []);

  const fetchSavedViolations = async () => {
    try {
      const response = await api.get('/saved-violations/');
      setViolationsByDate(response.data.violations_by_date);
      setError(null);
    } catch (err) {
      console.error('Fetch saved violations error:', err);
      setError("Failed to load saved violations.");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate("/");
  };

  const toggleFolder = (date) => {
    setExpandedFolders(prev => ({
      ...prev,
      [date]: !prev[date]
    }));
  };

  const downloadImage = (url, filename) => {
    const link = document.createElement('a');
    link.href = `http://localhost:8000${url}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getViolationTypeFromFilename = (filename) => {
    // Extract violation type from filename (e.g., "No_Helmet_uuid.jpg" -> "No Helmet")
    const parts = filename.split('_');
    if (parts.length >= 2) {
      return parts.slice(0, -1).join(' ').replace(/([A-Z])/g, ' $1').trim();
    }
    return "Unknown";
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading saved violations...</p>
        </div>
      </div>
    );
  }

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
          <h1 className="text-3xl font-bold text-center flex-1">Saved Violations</h1>
        </div>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded border-l-4 border-red-500 mb-8">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {Object.keys(violationsByDate).length > 0 ? (
          <div className="space-y-6">
            {Object.keys(violationsByDate).map((date) => (
              <div key={date} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                <button
                  onClick={() => toggleFolder(date)}
                  className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <Folder className="w-6 h-6 text-blue-500" />
                    <h2 className="text-xl font-semibold">{date}</h2>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      ({violationsByDate[date].length} violations)
                    </span>
                  </div>
                  {expandedFolders[date] ? (
                    <ChevronUp className="w-5 h-5" />
                  ) : (
                    <ChevronDown className="w-5 h-5" />
                  )}
                </button>

                {expandedFolders[date] && (
                  <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {violationsByDate[date].map((violation, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ duration: 0.3, delay: index * 0.1 }}
                          className="bg-gray-50 dark:bg-gray-700 rounded-lg overflow-hidden"
                        >
                          <div className="aspect-square relative">
                            <img
                              src={`http://localhost:8000${violation.url}`}
                              alt={`Violation ${index + 1}`}
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm font-medium">
                              {getViolationTypeFromFilename(violation.filename)}
                            </div>
                          </div>
                          <div className="p-3">
                            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300 mb-2">
                              <Calendar className="w-4 h-4" />
                              {formatDate(violation.timestamp)}
                            </div>
                            <button
                              onClick={() => downloadImage(violation.url, violation.filename)}
                              className="w-full px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded flex items-center justify-center gap-1"
                            >
                              <Download className="w-3 h-3" />
                              Save
                            </button>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <ImageIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">No Saved Violations</h2>
            <p className="text-gray-500 mb-6">No violations have been saved yet.</p>
            <button
              onClick={handleBack}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
            >
              Go to Dashboard
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
