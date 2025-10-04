import { useState, useEffect } from "react";
import api from "../utils/api";

export default function ViolationsTable({ videoFile }) {
	const [violations, setViolations] = useState([]);

	useEffect(() => {
		const fetchViolations = async () => {
			if (videoFile) {
				// Upload video and get violations from it
				const formData = new FormData();
				formData.append("file", videoFile);

				try {
					const res = await api.post("detect/", formData, {
						headers: { "Content-Type": "multipart/form-data" },
					});
					setViolations(res.data.violations || res.data); // normalize response
				} catch (error) {
					console.error("Error fetching violations:", error);
				}
			} else {
				// Optional: Fetch all past violations if no video is uploaded
				try {
					const res = await api.get("/api/violations/");
					setViolations(res.data.violations || res.data);
				} catch (error) {
					console.error("Error fetching all violations:", error);
				}
			}
		};

		fetchViolations();
	}, [videoFile]);

	if (!violations || violations.length === 0) {
		return <div className="p-4 text-center">Upload a video to see detected violations.</div>;
	}

	return (
		<div className="p-4">
			<h2 className="text-2xl font-bold mb-4 text-center">Detected Violations</h2>
			<div className="overflow-x-auto">
				<table className="min-w-full border border-gray-300 text-sm">
					<thead className="bg-gray-100">
						<tr>
							<th className="border px-4 py-2">#</th>
							<th className="border px-4 py-2">Timestamp</th>
							<th className="border px-4 py-2">Violation Type</th>
							<th className="border px-4 py-2">Detected Objects</th>
							<th className="border px-4 py-2">Violation Image</th>
							<th className="border px-4 py-2">License Plate</th>
						</tr>
					</thead>
					<tbody>
						{violations.map((violation, index) => (
							<tr key={index} className="text-center">
								<td className="border px-4 py-2">{index + 1}</td>
								<td className="border px-4 py-2">{violation.timestamp}</td>
								<td className="border px-4 py-2 font-medium text-red-600">{violation.violation_type}</td>
								<td className="border px-4 py-2">
									{Array.isArray(violation.labels) ? violation.labels.join(", ") : "N/A"}
								</td>
								<td className="border px-4 py-2 flex justify-center">
									<img
										src={`http://127.0.0.1:8000${violation.frame_image}`}
										alt={violation.violation_type}
										className="w-32 h-20 object-contain rounded"
									/>
								</td>
								<td className="border px-4 py-2">
									{violation.plate_image ? (
										<img
											src={`http://127.0.0.1:8000${violation.plate_image}`}
											alt="License Plate"
											className="w-32 h-20 object-contain mx-auto rounded"
										/>
									) : (
										<span>N/A</span>
									)}
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
}
