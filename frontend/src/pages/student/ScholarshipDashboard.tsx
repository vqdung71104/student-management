import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import ScholarshipModal from '../../components/ScholarshipModal';

interface Scholarship {
  id: number;
  title: string;
  type: string;
  slots: number;
  value_per_slot: number;
  sponsor: string;
  register_start_at: string;
  register_end_at: string;
  target_departments: string;
  target_courses: string;
  target_programs: string;
  contact_person: string;
  contact_info: string;
  document_url: string;
  description: string;
  note: string;
  created_at: string;
  updated_at: string;
}

interface ScholarshipApplication {
  id: number;
  scholarship_id: number;
  student_id: string;
  status: 'Chờ duyệt' | 'Đã duyệt' | 'Bị từ chối';
}

const StudentScholarshipDashboard: React.FC = () => {
  const { userInfo } = useAuth();
  const [scholarships, setScholarships] = useState<Scholarship[]>([]);
  const [applications, setApplications] = useState<ScholarshipApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [selectedScholarship, setSelectedScholarship] = useState<Scholarship | null>(null);
  const [showModal, setShowModal] = useState(false);

  // Fetch scholarships and applications
  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Get scholarships
      console.log('Fetching scholarships...');
      const scholarshipsResponse = await fetch('http://localhost:8000/api/scholarships/');
      if (scholarshipsResponse.ok) {
        const scholarshipsData = await scholarshipsResponse.json();
        console.log('Scholarships loaded:', scholarshipsData.length);
        setScholarships(scholarshipsData);
      } else {
        console.error('Failed to fetch scholarships:', scholarshipsResponse.status);
      }

      // Get user's applications
      console.log('Fetching applications...');
      const applicationsResponse = await fetch('http://localhost:8000/api/scholarship-applications/my-applications');
      console.log('Applications response status:', applicationsResponse.status);
      
      if (applicationsResponse.ok) {
        const applicationsData = await applicationsResponse.json();
        console.log('Applications data received:', applicationsData);
        console.log('Applications array length:', applicationsData.length);
        console.log('Current userInfo:', userInfo);
        setApplications(applicationsData);
        console.log('Applications set to state successfully');
      } else {
        console.error('Failed to fetch applications:', applicationsResponse.status, applicationsResponse.statusText);
        const errorText = await applicationsResponse.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter scholarships
  const filteredScholarships = scholarships.filter(scholarship => {
    const matchesSearch = scholarship.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = !selectedType || scholarship.type === selectedType;
    return matchesSearch && matchesType;
  });

  // Pagination
  const totalItems = filteredScholarships.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedScholarships = filteredScholarships.slice(startIndex, startIndex + itemsPerPage);

  // Get application status for scholarship
  const getApplicationStatus = (scholarshipId: number) => {
    const currentStudentId = userInfo?.student_id || "20225818"; // Fallback for testing
    console.log(`Checking status for scholarship ${scholarshipId}, student: ${currentStudentId}`);
    console.log('Available applications:', applications);

    const application = applications.find(app =>
      app.scholarship_id === scholarshipId && app.student_id === currentStudentId
    );
    
    console.log(`Found application:`, application);
    return application ? application.status : null;
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  // Handle view/apply for scholarship
  const handleViewScholarship = (scholarship: Scholarship) => {
    setSelectedScholarship(scholarship);
    setShowModal(true);
  };

  const handleApply = (scholarship: Scholarship) => {
    setSelectedScholarship(scholarship);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedScholarship(null);
  };

  // Get unique types for filter
  const uniqueTypes = [...new Set(scholarships.map(s => s.type))];

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Đang tải dữ liệu...</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Danh sách học bổng</h1>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
              >
                <option value="">Trạng thái học bổng</option>
                {uniqueTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div className="flex-1">
              <div className="flex">
                <input
                  type="date"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="DD/MM/YYYY"
                />
                <span className="px-3 py-2 bg-gray-100 border-t border-b border-gray-300 text-gray-500">
                  →
                </span>
                <input
                  type="date"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-r-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  placeholder="DD/MM/YYYY"
                />
              </div>
            </div>

            <div className="flex-1">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Tìm theo tên học bổng"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
              />
            </div>

            <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:ring-2 focus:ring-red-500">
              🔍
            </button>
          </div>
        </div>

        {/* Scholarships Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    STT
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Học bổng
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ĐV chủ trì
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    TG đăng ký
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    SL học bổng
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tài liệu
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trạng thái
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ghi chú
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedScholarships.map((scholarship, index) => {
                  const applicationStatus = getApplicationStatus(scholarship.id);
                  return (
                    <tr key={scholarship.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {startIndex + index + 1}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleViewScholarship(scholarship)}
                          className="text-blue-600 hover:text-blue-900 hover:underline font-medium text-left"
                        >
                          {scholarship.title}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {scholarship.sponsor}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(scholarship.register_start_at)} - {formatDate(scholarship.register_end_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {scholarship.slots}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {scholarship.document_url ? (
                          <a
                            href={scholarship.document_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-900 hover:underline"
                          >
                            File đính kèm
                          </a>
                        ) : (
                          <span className="text-gray-400">Không có</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {applicationStatus ? (
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            applicationStatus === 'Đã duyệt' ? 'bg-green-100 text-green-800' :
                            applicationStatus === 'Bị từ chối' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {applicationStatus}
                          </span>
                        ) : (
                          <button
                            onClick={() => handleApply(scholarship)}
                            className="px-4 py-2 bg-red-600 text-white text-xs font-semibold rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                          >
                            Đăng ký
                          </button>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {scholarship.note || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Trước
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                Sau
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Tổng <span className="font-medium">{totalItems}</span> Học bổng
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    &lt;
                  </button>
                  
                  {/* Page numbers */}
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          currentPage === pageNum
                            ? 'z-10 bg-red-50 border-red-500 text-red-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                  >
                    &gt;
                  </button>
                </nav>
              </div>
              <div>
                <select
                  value={itemsPerPage}
                  className="text-sm border-gray-300 rounded"
                >
                  <option value={10}>Hiển thị 10 dòng/trang</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scholarship Detail Modal */}
      {showModal && selectedScholarship && (
        <ScholarshipModal 
          scholarship={selectedScholarship}
          applicationStatus={getApplicationStatus(selectedScholarship.id)}
          onClose={closeModal}
          onApplicationSubmitted={() => {
            // Refresh applications after submission
            fetchData();
          }}
        />
      )}
    </div>
  );
};

export default StudentScholarshipDashboard;