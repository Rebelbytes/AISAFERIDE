import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
	ArrowLeft,
	FileText,
	User,
	Mail,
	Phone,
	MapPin,
	Calendar,
	AlertTriangle,
	CheckCircle,
	Printer,
} from "lucide-react";
import api from "../utils/api";

export default function ChallanGeneration() {
	const location = useLocation();
	const navigate = useNavigate();
	const [challanData, setChallanData] = useState(null);
	const [vehicleOwner, setVehicleOwner] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	// Get data from navigation state
	const { licensePlateNumber, violationType } = location.state || {};

	useEffect(() => {
		if (licensePlateNumber && violationType) {
			generateChallan();
		} else {
			setError("Missing required data for challan generation");
			setLoading(false);
		}
	}, [licensePlateNumber, violationType]);

	const generateChallan = async () => {
		try {
			setLoading(true);
			
			// Generate challan
			const response = await api.post("/challan/generate/", {
				vehicle_number: licensePlateNumber,
				violation_type: violationType,
			});

			setChallanData(response.data.challan);
			setVehicleOwner(response.data.vehicle_owner);
			setError(null);
		} catch (error) {
			console.error("Error generating challan:", error);
			setError("Failed to generate challan: " + (error.response?.data?.error || error.message));
		} finally {
			setLoading(false);
		}
	};

	const handleBack = () => {
		navigate(-1); // Go back to previous page
	};

	const handlePrint = () => {
		window.print();
	};

	if (loading) {
		return (
			<div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex items-center justify-center">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
					<p className="text-lg">Generating Challan...</p>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex items-center justify-center">
				<div className="text-center">
					<AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
					<h2 className="text-2xl font-bold text-red-600 mb-2">Error</h2>
					<p className="text-gray-600 dark:text-gray-400 mb-4">{error}</p>
					<button
						onClick={handleBack}
						className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
					>
						Go Back
					</button>
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
				className="max-w-4xl mx-auto"
			>
				{/* Header */}
				<div className="flex items-center justify-between mb-8">
					<div className="flex items-center gap-4">
						<button
							onClick={handleBack}
							className="flex items-center gap-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
						>
							<ArrowLeft className="w-5 h-5" />
							Back
						</button>
					</div>
					<h1 className="text-3xl font-bold text-center flex-1">Challan Generated</h1>
					<div className="flex gap-2">
						<button
							onClick={handlePrint}
							className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
						>
							<Printer className="w-5 h-5" />
							Print
						</button>
					</div>
				</div>

				{/* Challan Card */}
				<div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
					{/* Challan Header */}
					<div className="text-center mb-8 border-b pb-6">
						<div className="flex items-center justify-center gap-2 mb-2">
							<FileText className="w-8 h-8 text-blue-600" />
							<h2 className="text-2xl font-bold text-gray-900 dark:text-white">
								TRAFFIC CHALLAN
							</h2>
						</div>
						<p className="text-gray-600 dark:text-gray-400">
							Challan ID: #{challanData?.id} | Date: {challanData?.date_issued ? new Date(challanData.date_issued).toLocaleDateString() : 'N/A'}
						</p>
					</div>

					<div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
						{/* Violation Details */}
						<div className="space-y-6">
							<div className="bg-red-50 dark:bg-red-900/20 p-6 rounded-lg">
								<h3 className="text-lg font-semibold text-red-800 dark:text-red-300 mb-4 flex items-center gap-2">
									<AlertTriangle className="w-5 h-5" />
									Violation Details
								</h3>
								<div className="space-y-3">
									<div>
										<span className="text-sm text-gray-600 dark:text-gray-400">Vehicle Number:</span>
										<p className="text-xl font-bold text-gray-900 dark:text-white">{challanData?.vehicle_number}</p>
									</div>
									<div>
										<span className="text-sm text-gray-600 dark:text-gray-400">Violation Type:</span>
										<p className="text-lg font-semibold text-red-600">{challanData?.violation_type}</p>
									</div>
									<div>
										<span className="text-sm text-gray-600 dark:text-gray-400">Fine Amount:</span>
										<p className="text-2xl font-bold text-green-600">₹{challanData?.fine_amount}</p>
									</div>
									<div>
										<span className="text-sm text-gray-600 dark:text-gray-400">Status:</span>
										<p className="text-lg font-semibold text-yellow-600">{challanData?.status}</p>
									</div>
								</div>
							</div>

							{/* Challan Info */}
							<div className="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg">
								<h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
									<Calendar className="w-5 h-5" />
									Challan Information
								</h3>
								<div className="space-y-3">
									<div>
										<span className="text-sm text-gray-600 dark:text-gray-400">Challan ID:</span>
										<p className="font-semibold text-gray-900 dark:text-white">#{challanData?.id}</p>
									</div>
									<div>
										<span className="text-sm text-gray-600 dark:text-gray-400">Date Issued:</span>
										<p className="font-semibold text-gray-900 dark:text-white">
											{challanData?.date_issued ? new Date(challanData.date_issued).toLocaleString() : 'N/A'}
										</p>
									</div>
									{challanData?.notes && (
										<div>
											<span className="text-sm text-gray-600 dark:text-gray-400">Notes:</span>
											<p className="font-semibold text-gray-900 dark:text-white">{challanData.notes}</p>
										</div>
									)}
								</div>
							</div>
						</div>

						{/* Vehicle Owner Details */}
						<div className="space-y-6">
							{vehicleOwner ? (
								<div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg">
									<h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-4 flex items-center gap-2">
										<User className="w-5 h-5" />
										Vehicle Owner Details
									</h3>
									<div className="space-y-4">
										<div className="flex items-center gap-3">
											<User className="w-5 h-5 text-gray-500" />
											<div>
												<span className="text-sm text-gray-600 dark:text-gray-400">Owner Name:</span>
												<p className="font-semibold text-gray-900 dark:text-white">{vehicleOwner.owner_name}</p>
											</div>
										</div>
										<div className="flex items-center gap-3">
											<Mail className="w-5 h-5 text-gray-500" />
											<div>
												<span className="text-sm text-gray-600 dark:text-gray-400">Email:</span>
												<p className="font-semibold text-gray-900 dark:text-white">{vehicleOwner.email}</p>
											</div>
										</div>
										<div className="flex items-center gap-3">
											<Phone className="w-5 h-5 text-gray-500" />
											<div>
												<span className="text-sm text-gray-600 dark:text-gray-400">Phone:</span>
												<p className="font-semibold text-gray-900 dark:text-white">{vehicleOwner.phone}</p>
											</div>
										</div>
										<div className="flex items-center gap-3">
											<MapPin className="w-5 h-5 text-gray-500" />
											<div>
												<span className="text-sm text-gray-600 dark:text-gray-400">Address:</span>
												<p className="font-semibold text-gray-900 dark:text-white">{vehicleOwner.address}</p>
											</div>
										</div>
									</div>
								</div>
							) : (
								<div className="bg-yellow-50 dark:bg-yellow-900/20 p-6 rounded-lg">
									<h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-300 mb-4 flex items-center gap-2">
										<AlertTriangle className="w-5 h-5" />
										Vehicle Owner Not Found
									</h3>
									<p className="text-gray-600 dark:text-gray-400">
										No vehicle owner information found for license plate number <strong>{challanData?.vehicle_number}</strong>.
										The challan has been generated but owner details are not available in the database.
									</p>
								</div>
							)}

							{/* Action Buttons */}
							<div className="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg">
								<h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Actions</h3>
								<div className="flex gap-3">
									<button
										onClick={handlePrint}
										className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
									>
										<Printer className="w-5 h-5" />
										Print Challan
									</button>
									<button
										onClick={handleBack}
										className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-semibold"
									>
										Close
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</motion.div>
		</div>
	);
}
