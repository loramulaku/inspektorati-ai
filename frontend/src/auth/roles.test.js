import { describe, expect, it } from 'vitest'
import { ROLE_HOME, ROLE_LABEL, ROLE_TITLE } from './roles'

const ROLES = ['inspektor', 'drejtor', 'admin']

describe('roles', () => {
  it('sends every role to its own dashboard', () => {
    expect(ROLE_HOME).toEqual({ inspektor: '/inspektor', drejtor: '/drejtor', admin: '/admin' })
  })

  it('has an Albanian label and title for every role', () => {
    for (const role of ROLES) {
      expect(ROLE_LABEL[role]).toBeTruthy()
      expect(ROLE_TITLE[role]).toBeTruthy()
    }
    expect(ROLE_LABEL).toEqual({ inspektor: 'Inspektor', drejtor: 'Drejtor', admin: 'Admin' })
  })
})
