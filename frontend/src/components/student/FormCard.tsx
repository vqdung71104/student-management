import type { FormTemplate } from '../../pages/student/Forms'

interface FormCardProps {
  form: FormTemplate
  onClick: () => void
}

const FormCard = ({ form, onClick }: FormCardProps) => {
  return (
    <div 
      onClick={onClick}
      className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer h-[200px] flex flex-col"
    >
      <div className="flex-1">
        <h3 className="font-semibold text-gray-900 mb-3 text-sm leading-tight">
          {form.title}
        </h3>
        <p className="text-gray-600 text-xs leading-relaxed line-clamp-4">
          {form.description}
        </p>
      </div>
      
      <div className="mt-4 pt-4 border-t border-gray-100">
        <button className="w-full bg-blue-50 text-blue-600 py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-100 transition-colors">
          Xem đơn
        </button>
      </div>
    </div>
  )
}

export default FormCard
