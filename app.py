import streamlit as st

st.title("AR Try-On Demo")

# Embed HTML + JS AR code
ar_html = """
<video id="video" width="320" height="240" autoplay></video>
<script>
navigator.mediaDevices.getUserMedia({ video: true })
.then(function(stream) {
    document.getElementById('video').srcObject = stream;
})
.catch(function(err) { console.log("Error: " + err); });
</script>
"""
st.components.v1.html(ar_html, height=300)
