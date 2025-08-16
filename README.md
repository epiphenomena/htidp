# htidp - HyperText ID Protocol

RESTful API protocol for sharing contact information and keeping it up to date

This is a proposed email killer. But it accomplishes the task in stages.

## Plain VCARD, optional addl fields

The goal of HTIDP is to facilitate sharing standard VCARD information
such that each party controls what contact information they share with whom,
and can keep their contact information updated.

Alice, Bob and Org will be the example parties/users, either people or
companies/organizations/groups.

The goal of HTIDP is to make it easy for Alice, Bob and Org to easily give each
other access to up-to-date contact information. Bob should not need to type
Alice's phone number into his phone and then text her to make sure that he
has her number correct. She should not need to remember to open that text and
associate Bob's name with the nameless number that just texted her. Alice
should never have to repeatedly spell her email address to someone claiming to
represent Org over the phone. Bob should not need to send every person he
has a record of contacting an email saying that he has a new email address.

It is assumed:

- there are multiple servers hosting HTIDP compatible endpoints
- users may have multiple accounts with multiple servers
- Users have multiple client applications from which to CRUD their own records in their accounts on their hosts
- The interaction between a user's clients and their hosts is out of scope


The protocol is intended to be always backwards compatible --
existing endpoints may by extended by including additional data in responses,
and new endpoints may be added.

The protocol is also intended to support extension by clients and servers.


Basic story:

- Alice and Bob decide to share contact information
- Alice requests a link+token via the client app on her phone or computer
- Alice gives the link+token to Bob:
  - by showing him a QR code he can scan
  - via NFC or bluetooth
  - assuming it is simple enough: by writing it down or spelling it out loud
- Bob uses one of his clients to submit the link+token to one of his hosts
- Bob and Alice's servers use the HTIDP protocol to share/store information necessary to access current contact information

The HTID Protocol describes the link+token and the interaction between hosts.




- Alice's server records the token along with the timestamp of the request, and any other data useful for filtering incoming connection requests.
- Bob's host/server receives the link+token.
  - The link is a syntactically valid url for an HTTPS resource with no query parameters
    - It is intended that the url is not required to be kept secret
  - The token is string containing only url-safe characters. Bob's server records the token and related data so that later action on the connection request can be matched.
- Bob's server GETs the url, following any redirects
  - The GET request may use the Accept header to prefer JSON before HTML responses
- Whatever server ultimately processes the request returns either an html form or a JSON object containing:
  - the URL to POST the form or data to
  - a name or nickname selected by Alice
  - an optional msg (240 character max length) from Alice for possible display to Bob
- Bob's server may use the name and msg fields to send a request for confirmation from Bob via Bob's client
- Bob's server POSTs to the given URL the following form-data:
  - the token
  - Bob's selected name/nickname
  - an optional msg (240 characters max long) to potentially be displayed to Alice
  - a perma-URL for Alice's server to save and associate with Bob (must be HTTPS)
  - a public key, that may unique to the connection between Alice and Bob, to serve as Bob's passkey to Alice
  - and a URL for Alice's server to POST the same information back to Bob's server
- Alice's server receives the POSTed data, and verifies that the token is valid. The token is removed from the set of open tokens
- Alice's server may use the name/nickname and msg to send a request for confirmation from Alice via Alice's client
- Alice's server POSTs to the given URL the following form-data:
  - the token
  - a perma-URL for Bob's server to save and associate with Alice (must be HTTPS)
  - a public key, that may unique to the connection between Alice and Bob (the public portion of a "passkey"), to serve as Alice's passkey to Bob
- Alice's server stores:
  - Bob's name/nickname
  - Bob's perma-URL
  - Bob's public key
- Bob's server removes the token from the set of open tokens and stores
  - Alice's name/nickname
  - Alice's perma-URL
  - Alice's public key
- Alice or Bob's server may GET the other's perma-URL
  - the response is a passkey challenge requiring use of the stored public key
  - an accepted passkey responds with either HTML or JSON containing whatever portions of the one's VCARD they chose to share with the other
- The servers may also submit and respond HEAD requests containing a timestamp encrypted with the public key that responds indicating whether the VCARD information has changed since the timestamp
- The servers MUST conform to existing HTTPS standards for time-to-live, response caching

## Implementation

This repository includes a Python/FastAPI implementation of HTIDP.
See [README_IMPLEMENTATION.md](README_IMPLEMENTATION.md) for details on how to run and use the implementation.

The project now uses `pyproject.toml` for dependency management and can be installed using [uv](https://github.com/astral-sh/uv) for faster dependency resolution and installation.

## Future Enhancements

### Version 2 - Use addl fields for PGP public key: encrypt, sign, verify ID

### Version 3 - WEB-RTC: calls and data exchange

### Version 4 - Messaging