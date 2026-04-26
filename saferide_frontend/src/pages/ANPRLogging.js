import React, { useEffect, useState } from "react";
import { Truck, AlertTriangle, List, Send, ArrowLeft, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import api from "../utils/api";

const ANPRLogging = () => {
	const navigate = useNavigate();
	const [violations, setViolations] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		fetchViolations();
	}, []);

	const fetchViolations = async () => {
		try {
			setLoading(true);
			const response = await api.get("/violations/");
			console.log("Violations data:", response.data);
			const mappedViolations = response.data.map((violation, index) => ({
				...violation,
				id: violation.id,
				type: violation.violation_type,
				confidence: violation.confidence || 0,
				frame_image: violation.frame_image,
				license_plate_image: violation.license_plate_image,
				license_plate_number: violation.license_plate_number || "N/A",
				created_at: violation.created_at,
			}));
			setViolations(mappedViolations);
			setError(null);
		} catch (err) {
			console.error("Fetch violations error:", err);
			setError("Failed to load violations from database.");
		} finally {
			setLoading(false);
		}
	};

	// Separate frames with and without license plates
	const withLP = violations.filter((v) => v.license_plate_image);
	const withoutLP = violations.filter((v) => !v.license_plate_image);

	const handleSendToOCR = (plateImage, violationType) => {
		navigate("/ocr_upload", {
			state: {
				autoProcessImage: `http://127.0.0.1:8000${plateImage}`,
				violationType: violationType,
			},
		});
	};

	const handleBack = () => {
		navigate("/");
	};

	if (loading) {
		return (
			<div className="min-h-screen bg-gray-50 flex items-center justify-center">
				<div className="text-center">
					<Loader2 className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
					<p className="text-gray-600">Loading violations...</p>
				</div>
			</div>
		);
	}

	return (
		<div className="p-6 bg-gray-50 min-h-screen font-sans">
			<header className="mb-8">
				<button
					onClick={handleBack}
					className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 font-semibold mb-4 transition"
				>
					<ArrowLeft className="w-5 h-5" />
					Back to Dashboard
				</button>
				<h1 className="text-3xl font-extrabold text-indigo-800 flex items-center">
					<List className="w-8 h-8 mr-3" />
					ANPR & Violation Logs
				</h1>
				<p className="text-gray-600 mt-2">
					All detected violations with license plate and frame images
				</p>
			</header>

			{error && (
				<div className="mb-8 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg text-red-600">
					<p>{error}</p>
					<button
						onClick={fetchViolations}
						className="mt-2 text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 transition"
					>
						Retry
					</button>
				</div>
			)}

			{/* Table 1: Violations with License Plate */}
			<div className="mb-12">
				<h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b pb-2 flex items-center">
					<Truck className="w-6 h-6 mr-2 text-indigo-600" />
					Violations with License Plate ({withLP.length})
				</h2>
				{withLP.length === 0 ? (
					<div className="bg-white rounded-xl shadow-xl p-8 text-center text-gray-500">
						<p>No violations with license plates detected yet.</p>
					</div>
				) : (
					<div className="overflow-x-auto bg-white rounded-xl shadow-xl">
						<table className="min-w-full divide-y divide-gray-200">
							<thead className="bg-indigo-50">
								<tr>
									<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">
										ID
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">
										Frame
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">
										Timestamp
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">
										Violation
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">
										Confidence
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">
										License Plate No.
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">
										License Plate Image
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">
										Action
									</th>
								</tr>
							</thead>
							<tbody className="bg-white divide-y divide-gray-200">
								{withLP.map((v) => (
									<tr key={v.id} className="hover:bg-gray-50 transition duration-100">
										<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
											{v.id}
										</td>
										<td className="px-6 py-4 whitespace-nowrap">
											{v.frame_image && (
												<img
													src={`http://127.0.0.1:8000${v.frame_image}`}
													alt={`Frame ${v.id}`}
													className="w-32 h-auto rounded-md shadow-sm"
													onError={(e) => (e.target.style.display = "none")}
												/>
											)}
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
											{new Date(v.created_at).toLocaleString()}
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">
											{v.type}
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
											{(v.confidence * 100).toFixed(1)}%
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-indigo-600">
											{v.license_plate_number}
										</td>
										<td className="px-6 py-4 whitespace-nowrap">
											{v.license_plate_image && (
												<img
													src={`http://127.0.0.1:8000${v.license_plate_image}`}
													alt={`Plate ${v.id}`}
													className="w-24 h-auto rounded-sm shadow-md"
													onError={(e) => (e.target.style.display = "none")}
												/>
											)}
										</td>
										<td className="px-6 py-4 whitespace-nowrap">
											{v.license_plate_image && (
												<button
													onClick={() =>
														handleSendToOCR(v.license_plate_image, v.type)
													}
													className="bg-indigo-600 text-white text-xs px-3 py-1 rounded-md hover:bg-indigo-700 transition flex items-center gap-1"
												>
													<Send className="w-3 h-3" />
													Send to OCR
												</button>
											)}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				)}
			</div>

			{/* Table 2: Violations without License Plate */}
			<div className="mb-12">
				<h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b pb-2 flex items-center">
					<AlertTriangle className="w-6 h-6 mr-2 text-red-600" />
					Frames with Violation but No License Plate ({withoutLP.length})
				</h2>
				{withoutLP.length === 0 ? (
					<div className="bg-white rounded-xl shadow-xl p-8 text-center text-gray-500">
						<p>All detected violations have associated license plates.</p>
					</div>
				) : (
					<div className="overflow-x-auto bg-white rounded-xl shadow-xl">
						<table className="min-w-full divide-y divide-gray-200">
							<thead className="bg-red-50">
								<tr>
									<th className="px-6 py-3 text-left text-xs font-medium text-red-700 uppercase tracking-wider">
										ID
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-red-700 uppercase tracking-wider">
										Frame
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-red-700 uppercase tracking-wider">
										Timestamp
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-red-700 uppercase tracking-wider">
										Violation
									</th>
									<th className="px-6 py-3 text-left text-xs font-medium text-red-700 uppercase tracking-wider">
										Confidence
									</th>
								</tr>
							</thead>
							<tbody className="bg-white divide-y divide-gray-200">
								{withoutLP.map((v) => (
									<tr key={v.id} className="hover:bg-gray-50 transition duration-100">
										<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
											{v.id}
										</td>
										<td className="px-6 py-4 whitespace-nowrap">
											{v.frame_image && (
												<img
													src={`http://127.0.0.1:8000${v.frame_image}`}
													alt={`Frame ${v.id}`}
													className="w-32 h-auto rounded-md shadow-sm"
													onError={(e) => (e.target.style.display = "none")}
												/>
											)}
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
											{new Date(v.created_at).toLocaleString()}
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">
											{v.type}
										</td>
										<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
											{(v.confidence * 100).toFixed(1)}%
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
				)}
			</div>

			{/* Summary Stats */}
			{violations.length > 0 && (
				<div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
					<div className="bg-white rounded-xl shadow-lg p-6">
						<p className="text-gray-600 text-sm font-medium">Total Violations</p>
						<p className="text-3xl font-bold text-blue-600">{violations.length}</p>
					</div>
					<div className="bg-white rounded-xl shadow-lg p-6">
						<p className="text-gray-600 text-sm font-medium">With License Plate</p>
						<p className="text-3xl font-bold text-indigo-600">{withLP.length}</p>
					</div>
					<div className="bg-white rounded-xl shadow-lg p-6">
						<p className="text-gray-600 text-sm font-medium">Without License Plate</p>
						<p className="text-3xl font-bold text-red-600">{withoutLP.length}</p>
					</div>
				</div>
			)}
		</div>
	);
};

export default ANPRLogging;
