const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const mongoose = require('mongoose');

const app = express();
const port = 3000;

// Connect to MongoDB
mongoose.connect('mongodb://localhost/testimonials', { useNewUrlParser: true, useUnifiedTopology: true });

// Define Testimonial Schema
const testimonialSchema = new mongoose.Schema({
    name: String,
    review: String
});

const Testimonial = mongoose.model('Testimonial', testimonialSchema);

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Routes
app.get('/api/testimonials', async (req, res) => {
    try {
        const testimonials = await Testimonial.find();
        res.json(testimonials);
    } catch (error) {
        res.status(500).send('Error fetching testimonials');
    }
});

app.post('/api/testimonials', async (req, res) => {
    try {
        const newTestimonial = new Testimonial(req.body);
        await newTestimonial.save();
        res.status(201).send('Testimonial submitted');
    } catch (error) {
        res.status(500).send('Error submitting testimonial');
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
/////////////////////////////////////////////////////////////////////////////