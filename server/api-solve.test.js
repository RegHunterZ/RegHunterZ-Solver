const request = require('supertest');
const { expect } = require('chai');
const app = require('../app');

describe('POST /api/solve', function() {
  it('returns matches with capture groups', async function() {
    const res = await request(app)
      .post('/api/solve')
      .send({
        pattern: '(t)(est)',
        flags: 'g',
        text: 'test test other',
        maxResults: 10
      })
      .expect(200);

    expect(res.body.ok).to.be.true;
    expect(res.body.matches).to.be.an('array').with.length(2);
    expect(res.body.matches[0]).to.have.property('match', 'test');
    expect(res.body.matches[0]).to.have.property('groups').that.deep.equals(['t', 'est']);
    expect(res.body.count).to.equal(2);
  });

  it('returns named capture groups', async function() {
    const res = await request(app)
      .post('/api/solve')
      .send({
        pattern: '(?<first>t)(?<rest>est)',
        flags: 'g',
        text: 'test',
        maxResults: 5
      })
      .expect(200);

    expect(res.body.ok).to.be.true;
    expect(res.body.matches[0].named).to.deep.equal({ first: 't', rest: 'est' });
  });

  it('respects maxResults limit (default 100 and cap at 100)', async function() {
    const longText = Array.from({length:200}, (_,i) => 'a').join(' ') + ' test '.repeat(150);
    const res = await request(app)
      .post('/api/solve')
      .send({
        pattern: '\\btest\\b',
        flags: 'g',
        text: longText,
        maxResults: 1000
      })
      .expect(200);

    expect(res.body.ok).to.be.true;
    expect(res.body.count).to.be.at.most(100);
    expect(res.body.truncated).to.be.a('boolean');
  });

  it('returns 400 for invalid flags', async function() {
    const res = await request(app)
      .post('/api/solve')
      .send({
        pattern: 'a',
        flags: 'z', // invalid
        text: 'a'
      })
      .expect(400);

    expect(res.body.ok).to.be.false;
  });

  it('returns 400 for missing fields', async function() {
    const res = await request(app)
      .post('/api/solve')
      .send({ pattern: 'a' })
      .expect(400);
    expect(res.body.ok).to.be.false;
  });
});
