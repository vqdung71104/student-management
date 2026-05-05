import React from 'react'

const UserGuidePage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md">
        <div className="bg-blue-600 text-white p-6 rounded-t-lg">
          <h1 className="text-2xl font-bold">HƯỚNG DẪN SỬ DỤNG</h1>
          <p className="mt-2 text-sm text-blue-50">
            Website này dùng để gợi ý và lập kế hoạch đăng ký học phần/lớp. Chỉ mang tính tham khảo và{' '}
            <strong>không thay thế</strong> việc đăng ký thật trên hệ thống chính thức của nhà trường.
          </p>
        </div>

        <div className="p-6 space-y-8 text-gray-700">
          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">1) Tổng quan</h2>
            <p>
              Bạn có thể xem thông tin học tập, upload file điểm để tạo dữ liệu cá nhân, thử chọn học phần/lớp để xem
              thời khóa biểu mẫu và kiểm tra xung đột lịch.
            </p>
            <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
              <p className="font-medium text-yellow-900">Lưu ý quan trọng</p>
              <ul className="list-disc pl-5 mt-2 space-y-1 text-yellow-900">
                <li>“Đăng ký” trong website là đăng ký mẫu/lập kế hoạch, không phải đăng ký thật.</li>
                <li>Quyết định đăng ký thật vẫn thực hiện trên hệ thống chính thức.</li>
                <li>Dữ liệu bạn upload (ví dụ file điểm) được dùng để cá nhân hóa gợi ý.</li>
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">2) Luồng sử dụng nhanh</h2>
            <ol className="list-decimal pl-5 space-y-2">
              <li>Đăng nhập tài khoản sinh viên.</li>
              <li>
                Vào <strong>Học tập → Xem điểm</strong> để xem điểm và <strong>upload file điểm</strong> (làm dữ liệu cho
                gợi ý).
              </li>
              <li>
                Vào <strong>Học tập → Chương trình đào tạo</strong> để xem CTĐT và các học phần.
              </li>
              <li>
                Vào <strong>Lập kế hoạch đăng ký → Chọn học phần (mẫu)</strong> để chọn trước các môn dự định học.
              </li>
              <li>
                Vào <strong>Lập kế hoạch đăng ký → Chọn lớp (mẫu)</strong> để chọn lớp và kiểm tra lịch.
              </li>
              <li>
                Vào <strong>Học tập → Thời khóa biểu</strong> để xem thời khóa biểu mẫu bạn đã chọn.
              </li>
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">3) Học tập</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900">Thời khóa biểu</h3>
                <p>Hiển thị thời khóa biểu mẫu dựa trên các lớp bạn đã chọn.</p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Xem điểm (Upload điểm)</h3>
                <p>
                  Upload file điểm giúp hệ thống biết bạn đã học những học phần nào và kết quả ra sao để đưa ra gợi ý phù
                  hợp hơn.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Chương trình đào tạo</h3>
                <p>Xem học phần trong CTĐT để lên kế hoạch học kỳ.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">4) Lập kế hoạch đăng ký (mẫu)</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-gray-900">Chọn học phần (mẫu)</h3>
                <p>
                  Chọn trước các học phần dự định học để so sánh nhiều phương án và đánh giá khối lượng học tập/tiến độ.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Chọn lớp (mẫu)</h3>
                <p>Bạn có thể thử nhiều lớp để kiểm tra xem lịch có “ổn” không, ví dụ:</p>
                <ul className="list-disc pl-5 mt-2 space-y-1">
                  <li>Trùng giờ giữa các lớp (xung đột lịch).</li>
                  <li>Lịch quá dày trong một ngày/tuần.</li>
                  <li>Khoảng trống quá lớn giữa các ca học.</li>
                </ul>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">5) Chatbot</h2>
            <p>Chatbot có thể hỗ trợ hướng dẫn sử dụng, giải đáp thắc mắc và gợi ý kế hoạch học tập (tham khảo).</p>
            <div className="mt-3 bg-gray-50 border border-gray-200 p-4 rounded">
              Chatbot và website <strong>không</strong> có quyền đăng ký học phần/lớp thật thay bạn.
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">6) Hỗ trợ</h2>
            <ul className="list-disc pl-5 space-y-1">
              <li>
                <strong>Những câu hỏi thường gặp</strong>: các câu hỏi phổ biến khi sử dụng hệ thống.
              </li>
              <li>
                <strong>Phản hồi và góp ý</strong>: gửi lỗi, góp ý tính năng, hoặc phản ánh trải nghiệm cho admin.
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  )
}

export default UserGuidePage
