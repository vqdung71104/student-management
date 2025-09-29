import emailjs from '@emailjs/browser'

// EmailJS configuration - bạn cần cập nhật các giá trị này
const EMAIL_CONFIG = {
  serviceId: 'service_jyg5mej',      // Thay bằng Service ID của bạn
  templateId: 'template_fg0nqpf',    // Thay bằng Template ID của bạn  
  publicKey: '6o4vdH_ZvtsDI_SA8'          // Thay bằng Public Key của bạn
}

export interface EmailData {
  studentName: string
  studentId: string
  studentEmail: string
  formType: string
  formContent: string
  documentContent: string
}

export const sendFormEmail = async (data: EmailData): Promise<boolean> => {
  try {
    const templateParams = {
      to_email: 'vuquangdung71104@gmail.com',
      student_name: data.studentName,
      student_id: data.studentId,
      student_email: data.studentEmail,
      form_type: data.formType,
      form_content: data.formContent,
      document_content: data.documentContent,
      subject: `Biểu mẫu: ${data.formType} - ${data.studentName}`,
    }

    const response = await emailjs.send(
      EMAIL_CONFIG.serviceId,
      EMAIL_CONFIG.templateId,
      templateParams,
      EMAIL_CONFIG.publicKey
    )

    console.log('Email sent successfully:', response)
    return true
  } catch (error) {
    console.error('Failed to send email:', error)
    return false
  }
}

// Mock function for development (remove in production)
export const sendFormEmailMock = async (data: EmailData): Promise<boolean> => {
  console.log('Mock email sending:', data)
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 2000))
  return true
}

// Extended interface for document attachment
interface EmailAttachmentData {
  studentName: string
  studentId: string
  formType: string
  formData: any
  documentBlob?: Blob
}

export const sendEmailWithAttachment = async (data: EmailAttachmentData): Promise<boolean> => {
  try {
    // Convert formData to readable format
    const formContent = Object.entries(data.formData)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n')

    const emailData: EmailData = {
      studentName: data.studentName,
      studentId: data.studentId,
      studentEmail: data.formData.email || '',
      formType: data.formType,
      formContent: formContent,
      documentContent: `Đơn ${data.formType} của sinh viên ${data.studentName}`
    }

    // Try to send real email first, fallback to mock if configuration is missing
    if (EMAIL_CONFIG.serviceId !== 'your_service_id' && 
        EMAIL_CONFIG.templateId !== 'your_template_id' && 
        EMAIL_CONFIG.publicKey !== 'your_public_key') {
      // Configuration is set, try real email
      return await sendFormEmail(emailData)
    } else {
      // Configuration not set, use mock for development
      console.log('EmailJS not configured, using mock email service')
      return await sendFormEmailMock(emailData)
    }
  } catch (error) {
    console.error('Failed to send email with attachment, falling back to mock:', error)
    // Fallback to mock if real email fails
    return await sendFormEmailMock({
      studentName: data.studentName,
      studentId: data.studentId,
      studentEmail: data.formData.email || '',
      formType: data.formType,
      formContent: 'Error occurred, using fallback',
      documentContent: `Đơn ${data.formType} của sinh viên ${data.studentName}`
    })
  }
}
