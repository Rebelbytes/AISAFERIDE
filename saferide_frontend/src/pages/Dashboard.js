import { useState, useEffect } from "react";
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
	Shield,
	TrendingUp,
	Calendar,
	AlertTriangle,
} from "lucide-react";
import {
	BarChart,
	Bar,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	Legend,
	LineChart,
	Line,
	PieChart,
	Pie,
	Cell,
	ResponsiveContainer,
} from "recharts";
import api from "../utils/api";

// Predefined distinct colors for pie chart matching dashboard theme
const colors = [
	'hsl(210, 70%, 50%)', // Blue
	'hsl(240, 70%, 50%)', // Indigo
	'hsl(270, 70%, 50%)', // Purple
	'hsl(300, 70%, 50%)', // Magenta
	'hsl(330, 70%, 50%)', // Pink
	'hsl(180, 70%, 50%)', // Cyan
	'hsl(150, 70%, 50%)', // Teal
	'hsl(120, 70%, 50%)', // Green
	'hsl(90, 70%, 50%)', // Lime
	'hsl(60, 70%, 50%)', // Yellow
	'hsl(30, 70%, 50%)', // Orange
	'hsl(0, 70%, 50%)', // Red
];

export default function Dashboard() {
	const [darkMode, setDarkMode] = useState(false);
	const [activeSection, setActiveSection] = useState("dashboard");
	const [showAiModal, setShowAiModal] = useState(false);
	const [vehicleType, setVehicleType] = useState("");
	const [violationCategory, setViolationCategory] = useState("general");
	const [selectedFile, setSelectedFile] = useState(null);
	const [filePreview, setFilePreview] = useState(null);
	const [isLoading, setIsLoading] = useState(false);
	const [progress, setProgress] = useState(0);
	const [logs, setLogs] = useState([]);
	const [analyticsData, setAnalyticsData] = useState(null);
	const [loadingAnalytics, setLoadingAnalytics] = useState(false);

	const navigate = useNavigate();

	// Check if user is logged in, redirect to login if not
	useEffect(() => {
		if (!localStorage.getItem("access")) {
			navigate("/login");
		}
	}, [navigate]);

	// Fetch analytics data when analytics section is active
	useEffect(() => {
		if (activeSection === "analytics") {
			fetchAnalyticsData();
		}
	}, [activeSection]);

	const fetchAnalyticsData = async () => {
		setLoadingAnalytics(true);
		try {
			const response = await fetch("http://127.0.0.1:8000/api/analytics/", {
				method: "GET",
				headers: {
					"Content-Type": "application/json",
				},
			});

			if (!response.ok) {
				throw new Error("Failed to fetch analytics data");
			}

			const data = await response.json();
			setAnalyticsData(data);
		} catch (error) {
			console.error("Error fetching analytics:", error);
			// Set empty data on error
			setAnalyticsData({
				total_violations: 0,
				violations_by_type: {},
				violations_by_date: {},
				detailed_violations: []
			});
		} finally {
			setLoadingAnalytics(false);
		}
	};

	const handleFileChange = (e) => {
		const file = e.target.files[0];
		setSelectedFile(file);
		if (file && file.type.startsWith("image/")) {
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
			const response = await fetch("http://127.0.0.1:8000/api/detect/", {
				method: "POST",
				body: formData,
			});

			if (!response.ok) {
				throw new Error("Network response was not ok");
			}

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let dataBuffer = "";
			let finalData = null;

			let isStreaming = false;
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				dataBuffer += decoder.decode(value, { stream: true });
				const lines = dataBuffer.split("\n");
				dataBuffer = lines.pop() || ""; // Keep incomplete line

				for (const line of lines) {
					const trimmedLine = line.trim();
					if (trimmedLine === "") continue;

					if (trimmedLine.startsWith("ERROR:")) {
						alert("Error processing file: " + trimmedLine.slice(6));
						return;
					} else if (trimmedLine.startsWith("DATA:")) {
						isStreaming = true;
						try {
							const jsonStr = trimmedLine.slice(5).trim();
							finalData = JSON.parse(jsonStr);
							console.log("Parsed final data:", finalData);
						} catch (e) {
							console.error("Failed to parse JSON:", e, trimmedLine);
						}
					} else {
						// Progress line
						setLogs((prev) => {
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

			// If not streaming, parse the entire response as JSON
			if (!isStreaming) {
				try {
					finalData = JSON.parse(dataBuffer.trim());
					console.log("Parsed JSON data:", finalData);
				} catch (e) {
					console.error("Failed to parse response as JSON:", e, dataBuffer);
				}
			}

			if (finalData && finalData.violations && finalData.violations.length > 0) {
				console.log("Violations detected:", finalData.violations);
				navigate("/preview-detection", {
					state: {
						annotated_media: [finalData.annotated_video],
						violation_types: finalData.violations,
						violation_images: finalData.violations.map((v) => v.frame_image),
						originalFile: selectedFile,
					},
				});
			} else if (finalData) {
				console.log("No violations in data:", finalData);
				navigate("/preview-detection", {
					state: {
						annotated_media: [finalData.annotated_video],
						violation_types: [],
						violation_images: [],
						originalFile: selectedFile,
					},
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
			console.error("Fetch error:", error);
			alert("Error processing file: " + error.message);
		} finally {
			setIsLoading(false);
		}
	};

	const features = [
		{
			title: "Live Camera",
			description: "Stream cameras in real-time to monitor traffic and capture violations instantly.",
			icon: <Camera className="w-6 h-6 text-red-500" />,
		},
		{
			title: "AI Detection",
			description: "Detects helmet, triple-seat, red light, seat belt, wrong-side driving, and phone usage using AI.",
			icon: <Car className="w-6 h-6 text-blue-500" />,
		},
		{
			title: "ANPR & Logging",
			description: "Automatically captures vehicle details, logs violations, and sends notifications.",
			icon: <Mail className="w-6 h-6 text-green-500" />,
		},
		{
			title: "e-Challan",
			description: "Generates digital fines and e-challans automatically for detected violations.",
			icon: <FileText className="w-6 h-6 text-purple-500" />,
		},
	];

	return (
		<div className={`${darkMode ? "dark" : ""}`}>
			{/* Top Header */}
			<header className="bg-gradient-to-r from-blue-500 to-purple-600 shadow-xl p-4 flex items-center justify-between relative z-10">
				<div className="flex items-center gap-3">
					<motion.div
						whileHover={{ scale: 1.1, boxShadow: "0 0 20px rgba(255,255,255,0.5)" }}
						whileTap={{ scale: 0.95 }}
						className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-lg cursor-pointer"
					>
						<Shield className="w-6 h-6 text-white" />
					</motion.div>
					<motion.h1
						whileHover={{ scale: 1.05 }}
						className="text-2xl md:text-3xl font-bold text-white cursor-pointer"
					>

					</motion.h1>
				</div>
				{/* Dark/Light Mode Toggle in Header */}
				<motion.button
					whileHover={{ scale: 1.05 }}
					whileTap={{ scale: 0.95 }}
					onClick={() => setDarkMode(!darkMode)}
					className="flex items-center justify-center gap-3 p-3 rounded-xl bg-white/20 backdrop-blur-sm hover:bg-white/30 transition-all duration-300 shadow-lg"
				>
					{darkMode ? <Sun className="w-5 h-5 text-yellow-400 animate-spin" /> : <Moon className="w-5 h-5 text-blue-200 animate-pulse" />}
					<span className="font-medium text-white">{darkMode ? "Light Mode" : "Dark Mode"}</span>
				</motion.button>
			</header>

			<div className="min-h-screen transition-colors duration-500 bg-gradient-to-br from-blue-100 via-indigo-100 to-purple-100 dark:from-gray-900 dark:via-blue-900 dark:to-purple-900 text-gray-900 dark:text-gray-100 relative overflow-hidden">
				{/* Animated Background Elements */}
				<div className="absolute inset-0 overflow-hidden pointer-events-none">
					<div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-500/30 to-purple-500/30 rounded-full blur-3xl animate-pulse"></div>
					<div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-indigo-500/30 to-pink-500/30 rounded-full blur-3xl animate-pulse delay-1000"></div>
					<div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 rounded-full blur-3xl animate-pulse delay-500"></div>
					{/* Additional light mode elements */}
					<div className="absolute top-20 left-20 w-64 h-64 bg-gradient-to-br from-yellow-400/20 to-orange-400/20 rounded-full blur-2xl animate-bounce delay-300"></div>
					<div className="absolute bottom-20 right-20 w-48 h-48 bg-gradient-to-tl from-green-400/25 to-teal-400/25 rounded-full blur-2xl animate-pulse delay-700"></div>
				</div>

				<div className="flex flex-1">
					{/* Sidebar */}
					<aside className="w-64 h-screen bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl shadow-2xl p-6 flex flex-col transition-all duration-500 border-r border-white/20 dark:border-gray-700/50 relative z-10">
						{/* Sidebar Navigation */}
						<nav className="flex-1">
							<ul className="space-y-2">
								<li
									className={`flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all duration-300 group ${activeSection === "dashboard"
										? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-105"
										: "hover:bg-white/60 dark:hover:bg-gray-700/60 hover:shadow-lg hover:transform hover:scale-102"
										}`}
									onClick={() => setActiveSection("dashboard")}
								>
									<LayoutDashboard className={`w-5 h-5 transition-transform duration-300 ${activeSection === "dashboard" ? "rotate-12" : "group-hover:rotate-12"}`} />
									<span className="font-medium">Dashboard</span>
								</li>
								<li
									className={`flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all duration-300 group ${activeSection === "saved-violations"
										? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-105"
										: "hover:bg-white/60 dark:hover:bg-gray-700/60 hover:shadow-lg hover:transform hover:scale-102"
										}`}
									onClick={() => {
										setActiveSection("saved-violations");
										navigate("/saved-violations");
									}}
								>
									<Image className={`w-5 h-5 transition-transform duration-300 ${activeSection === "saved-violations" ? "rotate-12" : "group-hover:rotate-12"}`} />
									<span className="font-medium">Saved Violations</span>
								</li>
								<li
									className={`flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all duration-300 group ${activeSection === "profile"
										? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-105"
										: "hover:bg-white/60 dark:hover:bg-gray-700/60 hover:shadow-lg hover:transform hover:scale-102"
										}`}
									onClick={() => {
										setActiveSection("profile");
										navigate("/profile");
									}}
								>
									<Users className={`w-5 h-5 transition-transform duration-300 ${activeSection === "profile" ? "rotate-12" : "group-hover:rotate-12"}`} />
									<span className="font-medium">Profile</span>
								</li>
								<li
									className={`flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all duration-300 group ${activeSection === "analytics"
										? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-105"
										: "hover:bg-white/60 dark:hover:bg-gray-700/60 hover:shadow-lg hover:transform hover:scale-102"
										}`}
									onClick={() => setActiveSection("analytics")}
								>
									<BarChart3 className={`w-5 h-5 transition-transform duration-300 ${activeSection === "analytics" ? "rotate-12" : "group-hover:rotate-12"}`} />
									<span className="font-medium">Analytics</span>
								</li>
								<li
									className={`flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all duration-300 group ${activeSection === "about"
										? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-105"
										: "hover:bg-white/60 dark:hover:bg-gray-700/60 hover:shadow-lg hover:transform hover:scale-102"
										}`}
									onClick={() => setActiveSection("about")}
								>
									<Info className={`w-5 h-5 transition-transform duration-300 ${activeSection === "about" ? "rotate-12" : "group-hover:rotate-12"}`} />
									<span className="font-medium">About</span>
								</li>
							</ul>
						</nav>

						<button
							onClick={() => {
								localStorage.removeItem("access");
								navigate("/login");
							}}
							className="flex items-center gap-3 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 font-semibold p-4 rounded-xl transition-all duration-300 hover:bg-red-50 dark:hover:bg-red-900/20 hover:shadow-lg transform hover:scale-105"
						>
							<LogOut className="w-5 h-5" />
							<span>Logout</span>
						</button>
					</aside>

					{/* Main Content */}
					<main className="flex-1 p-8 relative z-10">

						{/* Conditional Content Based on Active Section */}
						{activeSection === "dashboard" && (
							<>
								{/* Hero / Project Info Section */}
								<motion.div
									initial={{ opacity: 0, y: -30 }}
									animate={{ opacity: 1, y: 0 }}
									transition={{ duration: 1 }}
									className="mb-12 text-center"
								>
									<motion.div
										whileHover={{
											scale: 1.2
										}}
										whileTap={{ scale: 0.85 }}
										className="inline-flex items-center gap-4 cursor-pointer transition-all duration-500 mb-6"
									>
										<div className="relative">
											<Shield className="w-12 h-12 text-blue-900 drop-shadow-2xl" />
										</div>
										<h2 className="text-4xl md:text-5xl font-extrabold text-blue-900 flex">
											{"SafeRide".split("").map((letter, index) => (
												<motion.span
													key={index}
													initial={{ opacity: 0, y: 20 }}
													animate={{ opacity: 1, y: 0 }}
													transition={{
														delay: index * 0.1,
														duration: 0.5,
														type: "spring",
														stiffness: 120
													}}
													className="inline-block"
												>
													{letter}
												</motion.span>
											))}
										</h2>
									</motion.div>
									<p className="mt-4 text-gray-700 dark:text-gray-300 max-w-2xl mx-auto text-lg">
										Monitor traffic in real-time, detect violations using AI, and automate e-challans to improve road safety
										efficiently.
									</p>
								</motion.div>

								{/* Features Grid */}
								<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
									{features.map((feature, idx) => (
										<motion.div
											key={idx}
											initial={{ opacity: 0, y: 30 }}
											whileHover={{ scale: 1.02 }}
											animate={{ opacity: 1, y: 0 }}
											transition={{ delay: idx * 0.2, type: "spring", stiffness: 120 }}
											className="relative bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-4 rounded-xl shadow-xl hover:shadow-2xl cursor-pointer border border-white/20 dark:border-gray-700/50 overflow-hidden group transition-all duration-500 transform-gpu"
											onClick={
												idx === 0 ? () => navigate("/live-detection") : idx === 1 ? () => setShowAiModal(true) : undefined
											}
										>
											{/* Animated gradient border */}
											<div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 p-[2px]">
												<div className="w-full h-full bg-white/95 dark:bg-gray-800/95 rounded-xl"></div>
											</div>

											{/* Floating particles effect */}
											<div className="absolute inset-0 overflow-hidden rounded-xl">
												<div className="absolute top-2 right-2 w-1 h-1 bg-blue-400 rounded-full animate-ping opacity-20"></div>
												<div className="absolute bottom-2 left-2 w-0.5 h-0.5 bg-purple-400 rounded-full animate-pulse opacity-30 delay-300"></div>
												<div className="absolute top-1/2 left-1/2 w-0.5 h-0.5 bg-pink-400 rounded-full animate-bounce opacity-25 delay-700"></div>
											</div>

											<div className="relative z-10">
												{/* Icon with glow effect */}
												<div className="mb-2 transform group-hover:scale-110 transition-transform duration-300">
													<div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/50 dark:to-purple-900/50 rounded-lg flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow duration-300">
														{feature.icon}
													</div>
												</div>

												<h3 className="text-base font-bold mb-1 bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
													{feature.title}
												</h3>
												<p className="text-base text-gray-600 dark:text-gray-400 leading-relaxed group-hover:text-gray-800 dark:group-hover:text-gray-200 transition-colors duration-300">
													{feature.description}
												</p>

												{/* Action indicator */}
												<div className="mt-2 flex items-center gap-1 text-xs font-medium text-blue-600 dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
													<span>Click to explore</span>
													<svg className="w-3 h-3 animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
													</svg>
												</div>
											</div>
										</motion.div>
									))}
								</div>
							</>
						)}

						{activeSection === "analytics" && (
							<motion.div
								initial={{ opacity: 0, y: 20 }}
								animate={{ opacity: 1, y: 0 }}
								transition={{ duration: 0.5 }}
								className="space-y-8"
							>
								{/* Analytics Header */}
								<div className="text-center mb-8">
									<motion.h2
										initial={{ scale: 0.9 }}
										animate={{ scale: 1 }}
										className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2"
									>
										Analytics Dashboard
									</motion.h2>
									<p className="text-gray-600 dark:text-gray-400">
										Comprehensive insights into traffic violations and safety metrics
									</p>
								</div>

								{loadingAnalytics ? (
									<div className="flex items-center justify-center py-12">
										<Loader2 className="w-8 h-8 animate-spin text-blue-500" />
										<span className="ml-2 text-gray-600 dark:text-gray-400">Loading analytics...</span>
									</div>
								) : analyticsData ? (
									<>
										{/* Key Metrics Cards */}
										<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
											<motion.div
												initial={{ opacity: 0, y: 20 }}
												animate={{ opacity: 1, y: 0 }}
												transition={{ delay: 0.1 }}
												className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-white/20 dark:border-gray-700/50"
											>
												<div className="flex items-center gap-4">
													<div className="w-12 h-12 bg-gradient-to-br from-red-500 to-pink-500 rounded-lg flex items-center justify-center">
														<AlertTriangle className="w-6 h-6 text-white" />
													</div>
													<div>
														<h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
															{analyticsData.total_violations || 0}
														</h3>
														<p className="text-gray-600 dark:text-gray-400">Total Violations</p>
													</div>
												</div>
											</motion.div>

											<motion.div
												initial={{ opacity: 0, y: 20 }}
												animate={{ opacity: 1, y: 0 }}
												transition={{ delay: 0.2 }}
												className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-white/20 dark:border-gray-700/50"
											>
												<div className="flex items-center gap-4">
													<div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
														<TrendingUp className="w-6 h-6 text-white" />
													</div>
													<div>
														<h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
															{(analyticsData.violations_by_type || []).length}
														</h3>
														<p className="text-gray-600 dark:text-gray-400">Violation Types</p>
													</div>
												</div>
											</motion.div>

											<motion.div
												initial={{ opacity: 0, y: 20 }}
												animate={{ opacity: 1, y: 0 }}
												transition={{ delay: 0.3 }}
												className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-white/20 dark:border-gray-700/50"
											>
												<div className="flex items-center gap-4">
													<div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-lg flex items-center justify-center">
														<Shield className="w-6 h-6 text-white" />
													</div>
													<div>
														<h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
															{(() => {
																const violations = analyticsData.violations_by_type || [];
																if (violations.length === 0) return 'N/A';
																const mostCommon = violations.reduce((max, current) =>
																	current.value > max.value ? current : max
																);
																return mostCommon.label.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
															})()}
														</h3>
														<p className="text-gray-600 dark:text-gray-400">Most Common Violation</p>
													</div>
												</div>
											</motion.div>

											<motion.div
												initial={{ opacity: 0, y: 20 }}
												animate={{ opacity: 1, y: 0 }}
												transition={{ delay: 0.4 }}
												className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-white/20 dark:border-gray-700/50"
											>
												<div className="flex items-center gap-4">
													<div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
														<Calendar className="w-6 h-6 text-white" />
													</div>
													<div>
														<h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
															{Object.keys(analyticsData.violations_by_date || {}).length}
														</h3>
														<p className="text-gray-600 dark:text-gray-400">Active Days</p>
													</div>
												</div>
											</motion.div>
										</div>

										{/* Charts Section */}
										<div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
											{/* Violations by Type Pie Chart */}
											<motion.div
												initial={{ opacity: 0, x: -20 }}
												animate={{ opacity: 1, x: 0 }}
												transition={{ delay: 0.4 }}
												className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-white/20 dark:border-gray-700/50"
											>
												<h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">
													Violations by Type
												</h3>
												<ResponsiveContainer width="100%" height={300}>
													<PieChart>
														<Pie
															data={(analyticsData.violations_by_type || []).map((item, index) => ({
																name: item.label.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
																value: item.value,
																fill: colors[index % colors.length]
															}))}
															cx="50%"
															cy="50%"
															labelLine={false}
															label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
															outerRadius={100}
															fill="#8884d8"
															dataKey="value"
														>
															{(analyticsData.violations_by_type || []).map((entry, index) => (
																<Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
															))}
														</Pie>
														<Tooltip
															contentStyle={{
																backgroundColor: darkMode ? '#1F2937' : '#FFFFFF',
																border: '1px solid #374151',
																borderRadius: '8px'
															}}
														/>
													</PieChart>
												</ResponsiveContainer>
											</motion.div>

											{/* Violations by Date and Time Bar Chart */}
											<motion.div
												initial={{ opacity: 0, x: 20 }}
												animate={{ opacity: 1, x: 0 }}
												transition={{ delay: 0.5 }}
												className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-white/20 dark:border-gray-700/50"
											>
												<h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">
													Violations by Date and Time
												</h3>
												<ResponsiveContainer width="100%" height={300}>
													<BarChart
														data={(() => {
															const dateMap = new Map();
															const getTimeSection = (hour) => {
																if (hour >= 6 && hour < 12) return 'Morning';
																if (hour >= 12 && hour < 18) return 'Afternoon';
																if (hour >= 18 && hour < 24) return 'Evening';
																return 'Night';
															};
															(analyticsData.detailed_violations || []).forEach(violation => {
																if (violation.timestamp) {
																	const date = new Date(violation.timestamp);
																	const dateStr = date.toLocaleDateString();
																	const hour = date.getHours();
																	const section = getTimeSection(hour);
																	if (!dateMap.has(dateStr)) {
																		dateMap.set(dateStr, { Morning: 0, Afternoon: 0, Evening: 0, Night: 0 });
																	}
																	dateMap.get(dateStr)[section] += 1;
																}
															});
															return Array.from(dateMap.entries())
																.sort(([a], [b]) => new Date(a) - new Date(b))
																.map(([date, sections]) => ({
																	date,
																	...sections
																}));
														})()}
													>
														<CartesianGrid strokeDasharray="3 3" stroke="#374151" />
														<XAxis
															dataKey="date"
															stroke="#6B7280"
															fontSize={12}
														/>
														<YAxis stroke="#6B7280" />
														<Tooltip
															contentStyle={{
																backgroundColor: darkMode ? '#1F2937' : '#FFFFFF',
																border: '1px solid #374151',
																borderRadius: '8px',
																padding: '12px'
															}}
															labelStyle={{ color: darkMode ? '#F9FAFB' : '#111827', fontWeight: 'bold', marginBottom: '8px' }}
															formatter={(value, name) => [
																value,
																name
															]}
															labelFormatter={(label) => `Date: ${label}`}
														/>
														<Legend
															wrapperStyle={{ paddingTop: '20px' }}
														/>
														<Bar
															dataKey="Morning"
															stackId="a"
															fill="#3B82F6"
															radius={[2, 2, 0, 0]}
														/>
														<Bar
															dataKey="Afternoon"
															stackId="a"
															fill="#10B981"
															radius={[2, 2, 0, 0]}
														/>
														<Bar
															dataKey="Evening"
															stackId="a"
															fill="#F59E0B"
															radius={[2, 2, 0, 0]}
														/>
														<Bar
															dataKey="Night"
															stackId="a"
															fill="#EF4444"
															radius={[2, 2, 0, 0]}
														/>
													</BarChart>
												</ResponsiveContainer>
											</motion.div>
										</div>

										{/* Recent Violations Table */}
										<motion.div
											initial={{ opacity: 0, y: 20 }}
											animate={{ opacity: 1, y: 0 }}
											transition={{ delay: 0.6 }}
											className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-white/20 dark:border-gray-700/50"
										>
											<h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">
												Recent Violations
											</h3>
											<div className="overflow-x-auto">
												<table className="w-full text-sm">
													<thead>
														<tr className="border-b border-gray-200 dark:border-gray-700">
															<th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">Type</th>
															<th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">Date</th>
															<th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">Time</th>
															<th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">Confidence</th>
														</tr>
													</thead>
													<tbody>
														{(analyticsData.detailed_violations || [])
															.slice(0, 10)
															.map((violation, index) => (
																<tr key={index} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
																	<td className="py-3 px-4 text-gray-900 dark:text-gray-100">
																		{violation.violation_type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'N/A'}
																	</td>
																	<td className="py-3 px-4 text-gray-600 dark:text-gray-400">
																		{violation.timestamp ? new Date(violation.timestamp).toLocaleDateString() : 'N/A'}
																	</td>
																	<td className="py-3 px-4 text-gray-600 dark:text-gray-400">
																		{violation.timestamp ? new Date(violation.timestamp).toLocaleTimeString() : 'N/A'}
																	</td>
																	<td className="py-3 px-4 text-gray-600 dark:text-gray-400">
																		{violation.confidence ? `${(violation.confidence * 100).toFixed(1)}%` : 'N/A'}
																	</td>
																</tr>
															))}
														{(analyticsData.detailed_violations || []).length === 0 && (
															<tr>
																<td colSpan="4" className="py-8 text-center text-gray-500 dark:text-gray-400">
																	No violations recorded yet
																</td>
															</tr>
														)}
													</tbody>
												</table>
											</div>
										</motion.div>
									</>
								) : (
									<div className="text-center py-12">
										<p className="text-gray-600 dark:text-gray-400">Failed to load analytics data</p>
									</div>
								)}
							</motion.div>
						)}

						{activeSection === "about" && (
							<div className="text-center">
								<h2 className="text-3xl font-bold mb-4">About SafeRide</h2>
								<p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
									SafeRide is an AI-powered traffic violation detection system designed to enhance road safety through automated monitoring and e-challan generation.
								</p>
							</div>
						)}
					</main>
				</div>
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
						<p className="mb-4 text-gray-700 dark:text-gray-300">
							Please select vehicle type and upload an image or video.
						</p>
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
									2 & 4 Wheeler
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
								<p className="mt-2 text-sm text-gray-500">
									Selected: {selectedFile.name} (Video preview not supported)
								</p>
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
