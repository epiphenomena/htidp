# htidp - HyperText ID Protocol

RESTful API protocol for sharing contact information and keeping it up to date

<https://jmap.io/spec-core.html>

This is a proposed email killer. But it accomplishes the task in stages.

Although there are versions of the protocol / API, backwards compatibility is required.
And capabilities should always be discoverable and flexible.
The server's responses should contain all of the information needed for a client
to determine what capabilities exist and which endpoints to GET/POST
with what information in order to exercise those capabilities.
Clients should simply ignore any capabilities that the client does not support.
Therefore, neither the URLs nor the data are versioned.

## Goals

The goal of HTIDP v1 is to facilitate sharing standard VCARD information
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
- Alice's email client refreshes the cached value for Bob's email address when requested after the cached value expires
- Bob's phone app refreshes the cached value for Alice's phone number when requested post expiry.

The HTID Protocol describes the link+token and the interaction between hosts.

## Version 0: Connection

Establish a connection between Alice and Bob. Root URL: any valid URL after following any redirects.

- GET: root ->
  - Challenge: id=challenge. Text contents
  - HTML form:
    - clientid = any string but preferably a uuid
    - challenge reponse: the challenge encrypted with the public key associated with the client id (proves that the client knows id and private key)
  - POSTing the form returns response not defined by version 1. This response is where the rest of the versions pick up. The point of v0 is that it can serve as the foundation of other protocols requiring a connection to be established.
- GET root/invite ->
  -

## Version 1: Plain VCARD, optional addl fields

- GET



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
  - an optional msg (utf-8 max length 240 characters) from Alice for possible display to Bob
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

This project contains a reference implementation consisting of a Go server and a Vanilla JS client.

### Project Structure
- `/server`: Reference server implementation (Go).
- `/client`: Reference client application (HTML/JS).
- `api_flow.md`: Detailed HATEOAS discovery and delegation flows.
- `schema_examples.json`: Example JSON payloads for the protocol.

### Running the Server
1. Navigate to the server directory: `cd server`
2. Build the server: `go build -o htidp-server .`
3. Run the server: `PORT=8000 ./htidp-server`

### Running the Client
Open `client/index.html` (Requestor) or `client/profile.html` (Profile Management) in your browser. 
Note: Ensure the server is running and the "Connected to" field matches your server's URL.

## Future Enhancements

### Version 2 - Use addl fields for PGP public key: encrypt, sign, verify ID

### Version 3 - WEB-RTC: calls and data exchange

### Version 4 - Messaging