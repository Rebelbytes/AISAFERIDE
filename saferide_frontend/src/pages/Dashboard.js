import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Car,
  Users,
  BarChart3,
  Info,
  LogOut,
  Camera,
  Mail,
  FileText,
  Sun,
  Moon,
  X,
  Upload,
  Loader2,
  Image,
} from "lucide-react";
import api from "../utils/api";

export default function Dashboard() {
  const [darkMode, setDarkMode] = useState(false);
  const [showAiModal, setShowAiModal] = useState(false);
  const [vehicleType, setVehicleType] = useState("");
  const [violationCategory, setViolationCategory] = useState("general");
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);

  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => setFilePreview(e.target.result);
      reader.readAsDataURL(file);
    } else {
      setFilePreview(null);
    }
  };

  const handleSubmit = async () => {
    if (!vehicleType || !selectedFile) {
      alert("Please select vehicle type and upload a file.");
      return;
    }

    if (vehicleType !== "2 wheeler") {
      alert("Currently only 2 wheeler detection is supported.");
      return;
    }

    setIsLoading(true);
    setProgress(0);
    setLogs([]);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("vehicle_type", vehicleType);
    formData.append("violation_category", violationCategory);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/detect/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let dataBuffer = '';
      let finalData = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        dataBuffer += decoder.decode(value, { stream: true });
        const lines = dataBuffer.split('\n');
        dataBuffer = lines.pop() || '';  // Keep incomplete line

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine === '') continue;

          if (trimmedLine.startsWith('ERROR:')) {
            alert('Error processing file: ' + trimmedLine.slice(6));
            return;
          } else if (trimmedLine.startsWith('DATA:')) {
            try {
              const jsonStr = trimmedLine.slice(5).trim();
              finalData = JSON.parse(jsonStr);
              console.log('Parsed final data:', finalData);
            } catch (e) {
              console.error('Failed to parse JSON:', e, trimmedLine);
            }
          } else {
            // Progress line
            setLogs(prev => {
              const newLogs = [...prev, trimmedLine];
              return newLogs.slice(-5); // Keep last 5
            });

            // Extract percentage
            const percentMatch = trimmedLine.match(/\((\d+\.?\d*)%\)/);
            if (percentMatch) {
              const percent = parseFloat(percentMatch[1]);
              setProgress(Math.min(percent, 100));
            }
          }
        }
      }

      if (finalData && finalData.violation_types && finalData.violation_types.length > 0) {
        console.log('Violations detected:', finalData.violation_types);
      } else if (finalData) {
        console.log('No violations in data:', finalData);
      }

      if (finalData) {
        navigate("/preview-detection", {
          state: {
            annotated_media: finalData.annotated_media || [],
            violation_types: finalData.violation_types || [],
            violation_images: finalData.violation_images || [],
            originalFile: selectedFile
          }
        });
      } else {
        alert("No data received from processing. Check console for details.");
      }

      setShowAiModal(false);
      setVehicleType("");
      setViolationCategory("general");
      setSelectedFile(null);
      setFilePreview(null);
    } catch (error) {
      console.error('Fetch error:', error);
      alert("Error processing file: " + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const features = [
    {
      title: "Live Camera",
      description:
        "Stream cameras in real-time to monitor traffic and capture violations instantly.",
      icon: <Camera className="w-6 h-6 text-red-500" />,
    },
    {
      title: "AI Detection",
      description:
        "Detects helmet, triple-seat, red light, seat belt, wrong-side driving, and phone usage using AI.",
      icon: <Car className="w-6 h-6 text-blue-500" />,
    },
    {
      title: "ANPR & Logging",
      description:
        "Automatically captures vehicle details, logs violations, and sends notifications.",
      icon: <Mail className="w-6 h-6 text-green-500" />,
    },
    {
      title: "e-Challan",
      description:
        "Generates digital fines and e-challans automatically for detected violations.",
      icon: <FileText className="w-6 h-6 text-purple-500" />,
    },
  ];

  return (
    <div className={`${darkMode ? "dark" : ""}`}>
      <div className="flex min-h-screen transition-colors duration-500 bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        {/* Sidebar */}
        <aside className="w-64 bg-white dark:bg-gray-800 shadow-lg p-6 flex flex-col transition-colors duration-500">
          <h1 className="text-2xl font-bold mb-8 flex items-center gap-2">
            <LayoutDashboard className="w-6 h-6 text-indigo-600 animate-bounce" />
            Dashboard
          </h1>
          <nav className="flex-1">
            <ul className="space-y-4">
              <li className="flex items-center gap-3 text-blue-600 font-semibold cursor-pointer hover:text-blue-800">
                <LayoutDashboard className="w-5 h-5" /> Dashboard
              </li>
              <li className="flex items-center gap-3 cursor-pointer hover:text-blue-800" onClick={() => navigate("/saved-violations")}>
                <Image className="w-5 h-5" /> Saved Violations
              </li>
              <li className="flex items-center gap-3 cursor-pointer hover:text-blue-800" onClick={() => navigate("/profile")}>
                <Users className="w-5 h-5" /> Profile
              </li>
              <li className="flex items-center gap-3 cursor-pointer hover:text-blue-800">
                <BarChart3 className="w-5 h-5" /> Analytics
              </li>
              <li className="flex items-center gap-3 cursor-pointer hover:text-blue-800">
                <Info className="w-5 h-5" /> About
              </li>
            </ul>
          </nav>
          <button className="flex items-center gap-2 text-red-600 hover:text-red-800 font-semibold mt-6">
            <LogOut className="w-5 h-5" /> Logout
          </button>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {/* Dark/Light Mode Toggle */}
          <div className="flex justify-end mb-4">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition"
            >
              {darkMode ? <Sun className="w-5 h-5 text-yellow-400" /> : <Moon className="w-5 h-5 text-gray-900" />}
              {darkMode ? "Light Mode" : "Dark Mode"}
            </button>
          </div>

          {/* Hero / Project Info Section */}
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="mb-12 text-center"
          >
            <h2 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 animate-gradient-x">
              SafeRide - AI Enabled Smart Road Safety Violation Detection And Monitoring System Using Neural Vision
            </h2>
            <p className="mt-4 text-gray-700 dark:text-gray-300 max-w-2xl mx-auto">
              Monitor traffic in real-time, detect violations using AI, and automate e-challans to improve road safety efficiently.
            </p>
          </motion.div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 30 }}
                whileHover={{ scale: 1.05 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.2, type: "spring", stiffness: 120 }}
                className="relative bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg hover:shadow-2xl cursor-pointer border-l-4 border-indigo-500 overflow-hidden group transition-colors duration-500"
                onClick={
                  idx === 0 
                    ? () => navigate("/live-detection") 
                    : idx === 1 
                    ? () => setShowAiModal(true) 
                    : undefined
                }
              >
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-100 via-purple-100 to-pink-100 opacity-0 group-hover:opacity-25 transition-opacity rounded-xl"></div>
                <div className="flex items-center gap-3 mb-3 relative z-10">
                  {feature.icon}
                  <h3 className="text-lg font-semibold">{feature.title}</h3>
                </div>
                <p className="relative z-10">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </main>
      </div>

      {/* AI Detection Modal */}
      {showAiModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="bg-white dark:bg-gray-800 p-8 rounded-xl shadow-2xl max-w-md w-full mx-4"
          >
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">AI Detection - Upload Image</h3>
              <button
                onClick={() => setShowAiModal(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <p className="mb-4 text-gray-700 dark:text-gray-300">Please select 2 wheeler and upload an image or video.</p>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Vehicle Type</label>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="vehicleType"
                    value="2 wheeler"
                    checked={vehicleType === "2 wheeler"}
                    onChange={(e) => setVehicleType(e.target.value)}
                    className="mr-2"
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
                  />
                  4 Wheeler
                </label>
              </div>
            </div>
            {vehicleType === "2 wheeler" && (
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Violation Type</label>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="violationCategory"
                      value="general"
                      checked={violationCategory === "general"}
                      onChange={(e) => setViolationCategory(e.target.value)}
                      className="mr-2"
                    />
                    General Violations (Helmet, Triple Seat, Wrong Side, Mobile)
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="violationCategory"
                      value="red_light"
                      checked={violationCategory === "red_light"}
                      onChange={(e) => setViolationCategory(e.target.value)}
                      className="mr-2"
                    />
                    Red Light Jumping
                  </label>
                </div>
              </div>
            )}
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">Upload Image or Video</label>
              <input
                type="file"
                accept="image/*,video/*"
                onChange={handleFileChange}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              {filePreview && (
                <div className="mt-4">
                  <img src={filePreview} alt="Preview" className="max-w-full h-48 object-cover rounded" />
                </div>
              )}
              {selectedFile && !filePreview && (
                <p className="mt-2 text-sm text-gray-500">Selected: {selectedFile.name} (Video preview not supported)</p>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSubmit}
                disabled={isLoading}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold py-2 px-4 rounded-lg flex items-center justify-center gap-2 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Analyze & Preview
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
