import React, { useEffect, useState } from "react";
import { Truck, AlertTriangle, List } from "lucide-react";
import { useLocation } from "react-router-dom";

const ViolationsTable = () => {
	const location = useLocation();
	const { violationsData = [], violationImages = [] } = location.state || {};
	const [violations, setViolations] = useState([]);

	useEffect(() => {
		// Map frontend data to include frame image and ID
		const mappedViolations = violationsData.map((v, index) => ({
			...v,
			type: v.violation_type,
			confidence: v.confidence || "Low Confidence",
			frame_image: violationImages[index] || null,
			id: index + 1, // fallback ID
			created_at: v.timestamp || new Date().toISOString(), // use timestamp if exists
		}));
		setViolations(mappedViolations);
	}, [violationsData, violationImages]);

	// Separate frames with and without license plates
	const withLP = violations.filter((v) => v.license_plate_image);
	const withoutLP = violations.filter((v) => !v.license_plate_image);

	return (
		<div className="p-6 bg-gray-50 min-h-screen font-sans">
			<header className="mb-8 flex justify-between items-center">
				<h1 className="text-3xl font-extrabold text-indigo-800 flex items-center">
					<List className="w-8 h-8 mr-3" />
					Complete Violation Log
				</h1>
			</header>

			{/* Table 1: Violations with License Plate */}
			<div className="mb-12">
				<h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b pb-2 flex items-center">
					<Truck className="w-6 h-6 mr-2 text-indigo-600" />
					Violations with License Plate ({withLP.length})
				</h2>
				<div className="overflow-x-auto bg-white rounded-xl shadow-xl">
					<table className="min-w-full divide-y divide-gray-200">
						<thead className="bg-indigo-50">
							<tr>
								<th className="px-6 py-3 text-left text-xs font-medium text-indigo-700 uppercase tracking-wider">ID</th>
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
									License Plate
								</th>
							</tr>
						</thead>
						<tbody className="bg-white divide-y divide-gray-200">
							{withLP.map((v) => (
								<tr key={v.id} className="hover:bg-gray-50 transition duration-100">
									<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{v.id}</td>
									<td className="px-6 py-4 whitespace-nowrap">
										{v.frame_image && (
											<img
												src={`http://127.0.0.1:8000${v.frame_image}`}
												alt={`Frame ${v.id}`}
												className="w-32 h-auto rounded-md shadow-sm"
											/>
										)}
									</td>
									<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
										{new Date(v.created_at).toLocaleString()}
									</td>
									<td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">{v.type}</td>
									<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
										{(v.confidence * 100).toFixed(1)}%
									</td>
									<td className="px-6 py-4 whitespace-nowrap">
										{v.license_plate_image && (
											<img
												src={`http://127.0.0.1:8000${v.license_plate_image}`}
												alt={`Plate ${v.id}`}
												className="w-24 h-auto rounded-sm shadow-md"
											/>
										)}
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</div>

			{/* Table 2: Violations without License Plate */}
			<div className="mb-12">
				<h2 className="text-2xl font-semibold text-gray-700 mb-4 border-b pb-2 flex items-center">
					<AlertTriangle className="w-6 h-6 mr-2 text-red-600" />
					Frames with Violation but No License Plate ({withoutLP.length})
				</h2>
				<div className="overflow-x-auto bg-white rounded-xl shadow-xl">
					<table className="min-w-full divide-y divide-gray-200">
						<thead className="bg-red-50">
							<tr>
								<th className="px-6 py-3 text-left text-xs font-medium text-red-700 uppercase tracking-wider">ID</th>
								<th className="px-6 py-3 text-left text-xs font-medium text-red-700 uppercase tracking-wider">Frame</th>
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
									<td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{v.id}</td>
									<td className="px-6 py-4 whitespace-nowrap">
										{v.frame_image && (
											<img
												src={`http://127.0.0.1:8000${v.frame_image}`}
												alt={`Frame ${v.id}`}
												className="w-32 h-auto rounded-md shadow-sm"
											/>
										)}
									</td>
									<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
										{new Date(v.created_at).toLocaleString()}
									</td>
									<td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">{v.type}</td>
									<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
										{(v.confidence * 100).toFixed(1)}%
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
};

export default ViolationsTable;
