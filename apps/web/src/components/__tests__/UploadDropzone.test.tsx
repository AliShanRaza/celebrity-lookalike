import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom';
import { UploadDropzone } from '../UploadDropzone';

describe('UploadDropzone 3-Step Sequential Flow Component Tests', () => {
  const defaultProps = {
    onFileSelected: vi.fn(),
    onSubmit: vi.fn(),
    isLoading: false,
  };

  it('Step 1: Renders gender selection cards initially; upload UI and origin UI are NOT rendered', () => {
    render(<UploadDropzone {...defaultProps} />);

    // Step 1 Gender cards must be visible
    expect(screen.getByTestId('step-gender-container')).toBeInTheDocument();
    expect(screen.getByTestId('gender-female-btn')).toBeInTheDocument();
    expect(screen.getByTestId('gender-male-btn')).toBeInTheDocument();

    // Step 2 Upload container and Step 3 Origin container MUST NOT exist
    expect(screen.queryByTestId('step-upload-container')).not.toBeInTheDocument();
    expect(screen.queryByTestId('step-origin-container')).not.toBeInTheDocument();
    expect(screen.queryByTestId('submit-matches-btn')).not.toBeInTheDocument();
  });

  it('Step 2: Selecting gender advances to upload dropzone; origin UI and submit button are still NOT rendered', () => {
    render(<UploadDropzone {...defaultProps} />);

    // Click Female
    fireEvent.click(screen.getByTestId('gender-female-btn'));

    // Step 1 Gender selection container hides, Step 2 Upload container renders
    expect(screen.queryByTestId('step-gender-container')).not.toBeInTheDocument();
    expect(screen.getByTestId('step-upload-container')).toBeInTheDocument();

    // Step 3 Origin container and submit button MUST NOT exist yet
    expect(screen.queryByTestId('step-origin-container')).not.toBeInTheDocument();
    expect(screen.queryByTestId('submit-matches-btn')).not.toBeInTheDocument();

    // Summary badge shows selected gender with a Change button
    expect(screen.getByText('Gender:')).toBeInTheDocument();
    expect(screen.getByText('female')).toBeInTheDocument();
  });

  it('Step 3: Uploading photo advances to origin selection; submit button is disabled until origin is chosen', () => {
    const { container } = render(<UploadDropzone {...defaultProps} />);

    // 1. Select Gender
    fireEvent.click(screen.getByTestId('gender-male-btn'));

    // 2. Upload Photo via hidden file input
    const file = new File(['fake-image-bytes'], 'portrait.jpg', { type: 'image/jpeg' });
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [file] } });

    // Step 2 Upload hides, Step 3 Origin container renders
    expect(screen.queryByTestId('step-upload-container')).not.toBeInTheDocument();
    expect(screen.getByTestId('step-origin-container')).toBeInTheDocument();
    expect(screen.getByTestId('origin-bollywood-btn')).toBeInTheDocument();
    expect(screen.getByTestId('origin-hollywood-btn')).toBeInTheDocument();

    // Submit button IS rendered but DISABLED
    const submitBtn = screen.getByTestId('submit-matches-btn');
    expect(submitBtn).toBeInTheDocument();
    expect(submitBtn).toBeDisabled();
  });

  it('Full Flow: Selecting origin enables submit button; clicking submit calls onSubmit with all 3 parameters', () => {
    const mockOnSubmit = vi.fn();
    const { container } = render(<UploadDropzone {...defaultProps} onSubmit={mockOnSubmit} />);

    // Step 1: Select Gender
    fireEvent.click(screen.getByTestId('gender-female-btn'));

    // Step 2: Select Photo
    const file = new File(['fake-image-bytes'], 'user_photo.jpg', { type: 'image/jpeg' });
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [file] } });

    // Step 3: Select Origin
    fireEvent.click(screen.getByTestId('origin-hollywood-btn'));

    // Submit Button is now ENABLED
    const submitBtn = screen.getByTestId('submit-matches-btn');
    expect(submitBtn).not.toBeDisabled();

    // Click Submit
    fireEvent.click(submitBtn);
    expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    expect(mockOnSubmit).toHaveBeenCalledWith(file, 'female', 'hollywood');
  });

  it('State Resets: Clicking Change link on Gender resets step back to Step 1 and clears all state', () => {
    const { container } = render(<UploadDropzone {...defaultProps} />);

    // Progress through to Step 3
    fireEvent.click(screen.getByTestId('gender-male-btn'));
    const file = new File(['fake-image'], 'photo.jpg', { type: 'image/jpeg' });
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(fileInput, { target: { files: [file] } });
    expect(screen.getByTestId('step-origin-container')).toBeInTheDocument();

    // Click "Change" link on Gender summary
    const changeGenderBtn = screen.getByRole('button', { name: 'Change gender selection' });
    fireEvent.click(changeGenderBtn);

    // Resets back to Step 1 Gender selection
    expect(screen.getByTestId('step-gender-container')).toBeInTheDocument();
    expect(screen.queryByTestId('step-upload-container')).not.toBeInTheDocument();
    expect(screen.queryByTestId('step-origin-container')).not.toBeInTheDocument();
  });
});
