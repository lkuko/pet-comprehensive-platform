import request from './request'

// 图片上传：subdir 可选 pets / products / avatars
export function uploadImage(file, subdir = 'pets') {
  const form = new FormData()
  form.append('file', file)
  form.append('subdir', subdir)
  return request.post('/upload/image', form)
}
