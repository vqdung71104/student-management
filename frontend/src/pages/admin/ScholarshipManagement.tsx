import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface Scholarship {
  id: number;
  title: string;
  type: string;
  slots: number;
  value_per_slot: number;
  sponsor?: string;
  register_start_at: string;
  register_end_at: string;
  target_departments?: string;
  target_courses?: string;
  target_programs?: string;
  contact_person?: string;
  contact_info?: string;
  document_url?: string;
  description?: string;
  note?: string;
  created_at: string;
  updated_at: string;
}

interface ScholarshipFormData {
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
}

const AdminScholarshipManagement: React.FC = () => {
  const [scholarships, setScholarships] = useState<Scholarship[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingScholarship, setEditingScholarship] = useState<Scholarship | null>(null);
  const [formData, setFormData] = useState<ScholarshipFormData>({
    title: '',
    type: '',
    slots: 0,
    value_per_slot: 0,
    sponsor: '',
    register_start_at: '',
    register_end_at: '',
    target_departments: '',
    target_courses: '',
    target_programs: '',
    contact_person: '',
    contact_info: '',
    document_url: '',
    description: '',
    note: ''
  });

  // Fetch scholarships
  const fetchScholarships = async () => {
    try {
      const response = await fetch('/api/scholarships/', {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setScholarships(data);
      } else {
        console.error('Failed to fetch scholarships');
      }
    } catch (error) {
      console.error('Error fetching scholarships:', error);
    }
  };

  useEffect(() => {
    fetchScholarships();
  }, []);

  // Reset form
  const resetForm = () => {
    setFormData({
      title: '',
      type: '',
      slots: 0,
      value_per_slot: 0,
      sponsor: '',
      register_start_at: '',
      register_end_at: '',
      target_departments: '',
      target_courses: '',
      target_programs: '',
      contact_person: '',
      contact_info: '',
      document_url: '',
      description: '',
      note: ''
    });
    setEditingScholarship(null);
    setShowForm(false);
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Prepare data with proper date format
      const submitData = {
        ...formData,
        register_start_at: formData.register_start_at + 'T00:00:00',
        register_end_at: formData.register_end_at + 'T23:59:59',
        slots: Number(formData.slots),
        value_per_slot: Number(formData.value_per_slot)
      };

      const url = editingScholarship 
        ? `/api/scholarships/${editingScholarship.id}` 
        : '/api/scholarships/';
        
      const method = editingScholarship ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
        },
        body: JSON.stringify(submitData),
      });

      if (response.ok) {
        alert(editingScholarship ? 'Cập nhật học bổng thành công!' : 'Tạo học bổng thành công!');
        resetForm();
        fetchScholarships(); // Refresh list
      } else {
        const errorData = await response.text();
        console.error('Error response:', errorData);
        alert(`Lỗi: ${response.status} - ${errorData}`);
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      alert('Có lỗi xảy ra khi gửi form');
    }
  };

  // Handle edit
  const handleEdit = (scholarship: Scholarship) => {
    setFormData({
      title: scholarship.title,
      type: scholarship.type,
      slots: scholarship.slots,
      value_per_slot: scholarship.value_per_slot,
      sponsor: scholarship.sponsor || '',
      register_start_at: scholarship.register_start_at.split('T')[0],
      register_end_at: scholarship.register_end_at.split('T')[0],
      target_departments: scholarship.target_departments || '',
      target_courses: scholarship.target_courses || '',
      target_programs: scholarship.target_programs || '',
      contact_person: scholarship.contact_person || '',
      contact_info: scholarship.contact_info || '',
      document_url: scholarship.document_url || '',
      description: scholarship.description || '',
      note: scholarship.note || ''
    });
    setEditingScholarship(scholarship);
    setShowForm(true);
  };

  // Handle delete
  const handleDelete = async (id: number) => {
    if (confirm('Bạn có chắc chắn muốn xóa học bổng này?')) {
      try {
        const response = await fetch(`/api/scholarships/${id}`, {
          method: 'DELETE',
        });

        if (response.ok) {
          alert('Xóa học bổng thành công!');
          fetchScholarships();
        } else {
          alert('Lỗi khi xóa học bổng');
        }
      } catch (error) {
        console.error('Error deleting scholarship:', error);
        alert('Có lỗi xảy ra khi xóa học bổng');
      }
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Quản lý Học bổng</h2>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Tạo học bổng mới
        </button>
      </div>

      {/* Scholarship List */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tiêu đề
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Loại
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Số lượng
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Giá trị/suất
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thời gian đăng ký
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thao tác
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {scholarships.map((scholarship) => (
                <tr key={scholarship.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {scholarship.title}
                    </div>
                    {scholarship.sponsor && (
                      <div className="text-sm text-gray-500">
                        {scholarship.sponsor}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      {scholarship.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {scholarship.slots}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {scholarship.value_per_slot.toLocaleString('vi-VN')} VND
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>{new Date(scholarship.register_start_at).toLocaleDateString('vi-VN')}</div>
                    <div>đến {new Date(scholarship.register_end_at).toLocaleDateString('vi-VN')}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => handleEdit(scholarship)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => handleDelete(scholarship.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Xóa
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-800">
                {editingScholarship ? 'Sửa học bổng' : 'Tạo học bổng mới'}
              </h3>
              <button
                onClick={resetForm}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tiêu đề học bổng *
                  </label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="Nhập tiêu đề học bổng"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Loại học bổng *
                  </label>
                  <select
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  >
                    <option value="">Chọn loại học bổng</option>
                    <option value="Học bổng nhà trường">Học bổng nhà trường</option>
                    <option value="Học bổng doanh nghiệp">Học bổng doanh nghiệp</option>
                    <option value="Học bổng chính phủ">Học bổng chính phủ</option>
                    <option value="Học bổng quốc tế">Học bổng quốc tế</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Số lượng suất *
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.slots}
                    onChange={(e) => setFormData({ ...formData, slots: parseInt(e.target.value) })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Giá trị mỗi suất (VND) *
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.value_per_slot}
                    onChange={(e) => setFormData({ ...formData, value_per_slot: parseInt(e.target.value) })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nhà tài trợ
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.sponsor}
                    onChange={(e) => setFormData({ ...formData, sponsor: e.target.value })}
                    placeholder="Tên nhà tài trợ"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Người liên hệ
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.contact_person}
                    onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                    placeholder="Tên người liên hệ"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ngày bắt đầu đăng ký *
                  </label>
                  <input
                    type="date"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.register_start_at}
                    onChange={(e) => setFormData({ ...formData, register_start_at: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ngày kết thúc đăng ký *
                  </label>
                  <input
                    type="date"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.register_end_at}
                    onChange={(e) => setFormData({ ...formData, register_end_at: e.target.value })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Đơn vị đích
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.target_departments}
                    onChange={(e) => setFormData({ ...formData, target_departments: e.target.value })}
                    placeholder="SOICT, SEEE, ..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Khóa học đích
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.target_courses}
                    onChange={(e) => setFormData({ ...formData, target_courses: e.target.value })}
                    placeholder="2022, 2023, 2024"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Chương trình đích
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.target_programs}
                    onChange={(e) => setFormData({ ...formData, target_programs: e.target.value })}
                    placeholder="ITE6, ICTU, ..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Thông tin liên hệ
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    value={formData.contact_info}
                    onChange={(e) => setFormData({ ...formData, contact_info: e.target.value })}
                    placeholder="Email, số điện thoại"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  URL tài liệu
                </label>
                <input
                  type="url"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.document_url}
                  onChange={(e) => setFormData({ ...formData, document_url: e.target.value })}
                  placeholder="https://example.com/document.pdf"
                />
              </div>

              {/* Description textarea - Key field for handling multiline text */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mô tả chi tiết
                </label>
                <textarea
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Nhập mô tả chi tiết về học bổng. Có thể chứa nhiều dòng và ký tự đặc biệt..."
                />
                <p className="text-sm text-gray-500 mt-1">
                  Có thể chứa văn bản dài với ký tự đặc biệt, xuống dòng, dấu câu...
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Ghi chú
                </label>
                <textarea
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={formData.note}
                  onChange={(e) => setFormData({ ...formData, note: e.target.value })}
                  placeholder="Ghi chú thêm..."
                />
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  {editingScholarship ? 'Cập nhật' : 'Tạo mới'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminScholarshipManagement;