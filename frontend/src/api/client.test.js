import { describe, expect, it } from 'vitest'
import { errorMessage } from './client'

describe('errorMessage', () => {
  it('uses the backend detail when it is a string', () => {
    const error = { response: { status: 401, data: { detail: 'Email ose fjalëkalim i pasaktë' } } }
    expect(errorMessage(error)).toBe('Email ose fjalëkalim i pasaktë')
  })

  it('joins FastAPI validation errors and drops the "Value error, " prefix', () => {
    const error = {
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ['body', 'password'], msg: 'Value error, Fjalëkalimi duhet të ketë të paktën 8 karaktere' },
            { loc: ['body', 'email'], msg: 'value is not a valid email address' },
          ],
        },
      },
    }
    expect(errorMessage(error)).toBe(
      'Fjalëkalimi duhet të ketë të paktën 8 karaktere · value is not a valid email address',
    )
  })

  it('explains when the server does not answer', () => {
    expect(errorMessage({ request: {} })).toBe('Serveri nuk përgjigjet. Kontrolloni që backend-i është i ndezur.')
  })

  it('falls back to a generic or given message', () => {
    expect(errorMessage({ response: { status: 500, data: {} } })).toBe('Diçka shkoi keq. Provoni përsëri.')
    expect(errorMessage({ response: { status: 500, data: {} } }, 'Gabim')).toBe('Gabim')
  })
})
